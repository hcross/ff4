#!/usr/bin/env python3
"""patch_impact — derive a ROM variant's dispatch profile from patch impact.

For each patch in ff4-port/patches/manifest.json (or one, via --patch-id):
byte-diff the vanilla image against the canonical patched image, intersect
the modified ranges with every dispatched routine's proven span
(registry/dispatch_ranges.json), propagate through the static call graph
(a native C body may inline the behaviour of its asm callees), honour the
frozen-data dependencies (registry/extra_ranges.json), and emit:

  - ff4-gnw/rom_profiles.c  (GENERATED: one {crc32 -> gated PCs} profile per
    known image; rom_ident.c arms the gate from it at ff4_init)
  - a human-review report on stdout (every gated entry with its reason;
    ALARM when the set exceeds the review threshold)
  - ff4-port/patches/out/<id>.impact.json (machine-readable detail)

Gating rules (fail-closed, see the translation-patch ADR):
  - level DELEG        -> exempt (the wrapper runs the ORIGINAL asm through
                          run_emulated_func, which reads the patched bytes)
  - resolved == false  -> always gated (no proven span; hint ranges are not
                          evidence)
  - proven span (+/- slop) intersects a modified range        -> gated
  - extra_ranges frozen-data region intersects a modified range -> gated
  - any transitive asm callee's span intersects a modified range -> gated
    (conservative: we cannot know per-body whether the C inlined the callee
    or delegates it; the oracle run on the patched ROM is the final judge)

The byte-diff is the truth for "modified": an IPS record that rewrites a
byte to its original value does not count, RLE/truncate quirks cannot skew
it, and the expansion area (beyond the vanilla size) is ignored — no
dispatched routine or callee can live there.

Usage:
    python3 registry/patch_impact.py [--patch-id ID] [--check]

--check : regenerate rom_profiles.c in memory and diff against the tracked
          file; exit 1 on drift (convention of render_registry.py --check).
          Requires the canonical variant images to be present (build them
          with apply_ips.py --patch-id <id> first).
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import gen_ranges  # noqa: E402  (label machinery + LoROM helpers, same toolset)

sys.path.insert(0, str(ROOT / "ff4-port" / "ca65-bridge"))
from ca65_bridge.backend import Ca65BridgeBackend  # noqa: E402  (pure stdlib pkg)

MANIFEST = ROOT / "ff4-port" / "patches" / "manifest.json"
RANGES = HERE / "dispatch_ranges.json"
EXTRA = HERE / "extra_ranges.json"
STATE = HERE / "dispatch_state.jsonl"
DISPATCH_ALL_C = ROOT / "ff4-gnw" / "dispatch_all.c"
PROFILES_C = ROOT / "ff4-gnw" / "rom_profiles.c"
UPSTREAM = ROOT / "ff4-port" / "upstream"

REVIEW_ALARM = 25  # human-review threshold on a variant's gated-set size


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------
def live_table_pcs() -> set[str]:
    """PCs actually present in the dispatch table. Comments stripped first:
    retired entries stay behind as tombstone comments that keep the
    '{ 0xPC, name }' shape (same rule as migrate_registry.cross_check)."""
    text = DISPATCH_ALL_C.read_text(errors="replace")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return set(m.group(1).upper()
               for m in re.finditer(r"\{\s*0x([0-9A-Fa-f]{6})\s*,", text))


def byte_diff_ranges(vanilla: bytes, patched: bytes) -> list[list[int]]:
    """Merged half-open [start, end) file ranges where the images differ,
    limited to the vanilla extent (expansion area is not gate-relevant)."""
    n = min(len(vanilla), len(patched))
    ranges: list[list[int]] = []
    i = 0
    while i < n:
        if vanilla[i] == patched[i]:
            i += 1
            continue
        j = i + 1
        while j < n and vanilla[j] != patched[j]:
            j += 1
        ranges.append([i, j])
        i = j
    return ranges


def overlaps(start: int, end_incl: int, mod: list[list[int]], slop: int) -> bool:
    """Does [start-slop, end_incl+slop] intersect any modified range?"""
    lo, hi = start - slop, end_incl + slop + 1  # half-open
    idx = bisect.bisect_right(mod, [lo]) - 1
    for s, e in mod[max(idx, 0):]:
        if s >= hi:
            break
        if e > lo:
            return True
    return False


def snes_colon_to_file(s: str) -> int:
    """'bank:addr' (extra_ranges convention) -> flat file offset."""
    bank, addr = s.split(":")
    return gen_ranges.file_offset((int(bank, 16) << 16) | int(addr, 16))


# --------------------------------------------------------------------------
# Call-graph closure
# --------------------------------------------------------------------------
class Closure:
    """Transitive asm-callee walk with memoized per-label verdicts."""

    def __init__(self, bridge: Ca65BridgeBackend, name_to_addr: dict[str, int],
                 addrs: list[int], mod: list[list[int]], slop: int):
        self.bridge = bridge
        self.name_to_addr = name_to_addr
        self.addrs = addrs
        self.mod = mod
        self.slop = slop
        self._memo: dict[str, str | None] = {}

    def _label_span_hit(self, label: str) -> bool:
        addr = self.name_to_addr.get(label)
        if addr is None:
            return False  # unknown target (indirect/computed): nothing to test
        end = gen_ranges._next_bound(self.addrs, addr)
        return overlaps(gen_ranges.file_offset(addr),
                        gen_ranges.file_offset(end), self.mod, self.slop)

    def modified_callee(self, label: str, _stack: frozenset[str] = frozenset()) -> str | None:
        """First modified label reachable from `label` (excl. itself), or None."""
        if label in self._memo:
            return self._memo[label]
        if label in _stack:  # recursion cycle
            return None
        self._memo[label] = None  # provisional (cycle-safe)
        stack = _stack | {label}
        for xref in self.bridge.xrefs_from(label):
            tgt = xref.name
            if tgt not in self.name_to_addr:
                continue
            if self._label_span_hit(tgt):
                self._memo[label] = tgt
                return tgt
            deeper = self.modified_callee(tgt, stack)
            if deeper is not None:
                self._memo[label] = f"{tgt} -> {deeper}"
                return self._memo[label]
        return self._memo[label]


# --------------------------------------------------------------------------
# Per-patch analysis
# --------------------------------------------------------------------------
def analyze_patch(entry: dict, identity: dict, ranges_doc: dict, extra_doc: dict,
                  table_pcs: set[str], bridge: Ca65BridgeBackend,
                  labels: dict[int, list[str]]) -> dict:
    vanilla_path = UPSTREAM.parent.parent / "ff4-port" / identity["file_hint"]
    variant_path = MANIFEST.parent / "out" / entry["output"]["file"]
    if not variant_path.is_file():
        raise FileNotFoundError(
            f"{variant_path} missing — build it first: "
            f"python3 ff4-port/patches/apply_ips.py --patch-id {entry['id']}")
    vanilla = vanilla_path.read_bytes()
    patched = variant_path.read_bytes()
    for blob, want, what in ((vanilla, identity["crc32"], "vanilla"),
                             (patched, entry["output"]["crc32"], "variant")):
        got = f"{zlib.crc32(blob) & 0xFFFFFFFF:08X}"
        if got != want:
            raise ValueError(f"{what} image CRC32 {got} != manifest {want}")

    mod = byte_diff_ranges(vanilla, patched)
    slop = ranges_doc["slop"]

    addrs = sorted(labels)
    name_to_addr: dict[str, int] = {}
    for addr, names in labels.items():
        for nm in names:
            name_to_addr.setdefault(nm, addr)
    closure = Closure(bridge, name_to_addr, addrs, mod, slop)

    extra_by_id: dict[str, list[dict]] = {}
    for x in extra_doc["entries"]:
        extra_by_id.setdefault(x["dispatch_id"], []).append(x)

    gated: list[dict] = []
    exempt_deleg: list[str] = []
    for r in ranges_doc["entries"]:
        if r["pc"] not in table_pcs:
            continue  # RETIRED tombstones etc. — nothing to gate
        reasons: list[str] = []
        if r["level"] == "DELEG":
            exempt_deleg.append(r["id"])
            continue
        if not r["resolved"]:
            reasons.append("unresolved range (fail-closed)")
        else:
            if overlaps(r["file_start"], r["file_end"], mod, slop):
                reasons.append("code range modified")
            for x in extra_by_id.get(r["id"], []):
                for rng in x["ranges"]:
                    if overlaps(snes_colon_to_file(rng["start"]),
                                snes_colon_to_file(rng["end"]), mod, slop):
                        reasons.append(f"frozen data modified ({rng['start']}-{rng['end']})")
            if not reasons and r["source_label"]:
                hit = closure.modified_callee(r["source_label"].split("/")[0])
                if hit:
                    reasons.append(f"callee modified: {hit}")
        if reasons:
            gated.append({"id": r["id"], "pc": r["pc"], "name": r["name"],
                          "level": r["level"], "reasons": reasons})

    gated.sort(key=lambda g: g["pc"])
    return {
        "patch_id": entry["id"],
        "crc32": entry["output"]["crc32"],
        "short_name": entry.get("short_name", entry["id"]),
        "modified_ranges": len(mod),
        "modified_bytes": sum(e - s for s, e in mod),
        "gated": gated,
        "exempt_deleg": sorted(exempt_deleg),
    }


# --------------------------------------------------------------------------
# rom_profiles.c generation
# --------------------------------------------------------------------------
HEADER = """\
/* GENERATED by registry/patch_impact.py -- do not edit by hand.
 * (Initial vanilla-only seed authored in the generator's exact format; the
 * first patch-impact run regenerates this file and `--check` guards drift.)
 *
 * One entry per known ROM image. `gated_pcs` lists the dispatch entry PCs
 * whose original asm the patch rewrote (range overlap + transitive-callee
 * closure, DELEG-exempt); rom_ident.c maps them to table slots at init.
 * Only the exact proof-base image (FF4 JP rev 1.1) is `is_vanilla` -- other
 * clean revisions (e.g. JP rev 1.0) are deliberately UNKNOWN: the native
 * bodies were never proven against their bytes. */

#include "rom_profiles.h"
#include <stddef.h>
"""

VANILLA_ENTRY = """\
    {
        /* Final Fantasy IV (Japan) rev 1.1, unheadered -- the proof base. */
        .crc32 = 0xCAA15E97u,
        .name = "FF4 JP 1.1 (vanilla)",
        .is_vanilla = 1,
        .gated_pcs = NULL,
        .gated_count = 0,
    },
"""


def render_profiles_c(analyses: list[dict]) -> str:
    out = [HEADER]
    for a in analyses:
        ident = "k_gated_" + re.sub(r"[^a-zA-Z0-9]", "_", a["patch_id"])
        pcs = [g["pc"] for g in a["gated"]]
        out.append(f"\n/* {a['short_name']}: {len(pcs)} gated of the dispatch table"
                   f" (see registry/patch_impact.py report). */\n")
        out.append(f"static const uint32_t {ident}[] = {{\n")
        for i in range(0, len(pcs), 6):
            row = ", ".join(f"0x{pc}u" for pc in pcs[i:i + 6])
            out.append(f"    {row},\n")
        out.append("};\n")
    out.append("\nconst ff4_rom_profile_t ff4_rom_profiles[] = {\n")
    out.append(VANILLA_ENTRY)
    for a in analyses:
        ident = "k_gated_" + re.sub(r"[^a-zA-Z0-9]", "_", a["patch_id"])
        out.append(f"""    {{
        .crc32 = 0x{a['crc32']}u,
        .name = "{a['short_name']}",
        .is_vanilla = 0,
        .gated_pcs = {ident},
        .gated_count = {len(a['gated'])},
    }},
""")
    out.append("""};

const int ff4_rom_profile_count =
    (int)(sizeof(ff4_rom_profiles) / sizeof(ff4_rom_profiles[0]));
""")
    return "".join(out)


def print_report(a: dict, state_notes: dict[str, str]) -> None:
    print(f"\n=== {a['patch_id']} (crc32 {a['crc32']}) ===")
    print(f"modified: {a['modified_bytes']} bytes in {a['modified_ranges']} ranges")
    print(f"gated: {len(a['gated'])}  |  DELEG exempt: {len(a['exempt_deleg'])}")
    if len(a["gated"]) > REVIEW_ALARM:
        print(f"!! ALARM: gated set exceeds the review threshold ({REVIEW_ALARM}) — "
              f"review below for hot routines before shipping this profile")
    for g in a["gated"]:
        note = state_notes.get(g["id"], "")
        note = (note[:100] + "…") if len(note) > 100 else note
        print(f"  {g['id']}  {g['name']:<28} {g['level']:<5} {'; '.join(g['reasons'])}"
              + (f"\n           registry: {note}" if note else ""))


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--patch-id", help="analyze one manifest entry (default: all)")
    ap.add_argument("--check", action="store_true",
                    help="regenerate rom_profiles.c in memory and diff; exit 1 on drift")
    args = ap.parse_args(argv)

    manifest = json.loads(MANIFEST.read_text())
    ranges_doc = json.loads(RANGES.read_text())
    extra_doc = json.loads(EXTRA.read_text())
    patches = [p for p in manifest["patches"]
               if not args.patch_id or p["id"] == args.patch_id]
    if args.patch_id and not patches:
        known = ", ".join(p["id"] for p in manifest["patches"])
        sys.stderr.write(f"error: unknown patch id (known: {known})\n")
        return 2

    gen_ranges.build_labels()  # ensures the proven .dbg exists (idempotent)
    labels = gen_ranges.parse_labels(gen_ranges.DBG)
    bridge = Ca65BridgeBackend(UPSTREAM)
    table_pcs = live_table_pcs()
    state_notes = {json.loads(l)["id"]: json.loads(l).get("notes", "")
                   for l in STATE.read_text().splitlines() if l.strip()}

    try:
        analyses = [analyze_patch(p, manifest["rom_identities"][p["base"]],
                                  ranges_doc, extra_doc, table_pcs, bridge, labels)
                    for p in patches]
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    rendered = render_profiles_c(analyses)

    if args.check:
        if args.patch_id:
            sys.stderr.write("error: --check runs on the full manifest (no --patch-id)\n")
            return 2
        if rendered != PROFILES_C.read_text():
            sys.stderr.write(f"drift: {PROFILES_C} does not match a fresh generation\n")
            return 1
        print(f"rom_profiles.c up to date ({len(analyses)} variant profiles)")
        return 0

    for a in analyses:
        print_report(a, state_notes)
        impact_path = MANIFEST.parent / "out" / f"{a['patch_id']}.impact.json"
        impact_path.write_text(json.dumps(a, indent=2) + "\n")
        print(f"  detail: {impact_path}")

    if not args.patch_id:
        PROFILES_C.write_text(rendered)
        print(f"\nwrote {PROFILES_C}")
    else:
        print("\n(single-patch run: rom_profiles.c NOT rewritten — run without "
              "--patch-id to regenerate all profiles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
