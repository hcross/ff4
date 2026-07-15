#!/usr/bin/env python3
"""gen_ranges — derive per-dispatched-routine SNES address ranges from the
buildable reference disassembly, so a later impact tool can intersect them
with a translation patch's modified byte ranges.

The routine entry PCs come from ``registry/dispatch_state.jsonl`` (entry
points only, no extents). This script bounds each routine by re-deriving the
full symbol table of the vendored ca65 disassembly (``ff4-port/upstream``),
then writes ``registry/dispatch_ranges.json``.

How the labels are obtained (and proven against the true ROM bytes)
-------------------------------------------------------------------
``registry/dispatch_state.jsonl`` stores only entry PCs. To get routine
*extents* we need every routine/data label with its linked address. The
vendored objects were assembled without ``-g`` (no symbol/debug records), and
the VICE label dump (``ld65 -Ln``) only carries the ~40 exported symbols — far
too few to bound ~215 routines. So this script performs an **out-of-band**
build entirely inside a gitignored scratch dir (``registry/.ranges-build/``),
never touching the vendored tree:

  1. Re-assemble each module with ``ca65 -g`` and the exact jp1 flags
     (``-D BUGFIX_WORLD_BATTLE=1 -D ROM_VERSION=1``) into the scratch dir.
  2. Re-link with ``ld65 --dbgfile`` reusing the vendored ``ff4-jp.lnk`` config.
  3. **Prove** the relinked image against the tracked ``rom/ff4-jp1.sfc``: the
     only bytes allowed to differ are the 4-byte internal-header checksum pair
     (file 0x7FDC-0x7FDF). Every other byte must be identical, which proves the
     label addresses are computed against the true ROM bytes. Those 4 bytes are
     then copied from the tracked ROM so the scratch image CRC32 == CAA15E97.

Adding ``-g`` changes only the object's debug records, never the emitted bytes,
so the proof above holds. This avoids the annotation-comment addresses in
``notes/ff4j-sfc.asm`` entirely (those drift +2 on ~6 routines and omit banks
08/0E/12/1E — see AGENTS.md).

Boundary policy
---------------
A routine's range is ``[entry, next_label - 1]`` where ``next_label`` is the
nearest **routine-level** label strictly after the entry *in the same bank*.
Routine-level = a named (non ``@``-prefixed) ``lab`` symbol; the ``@``-prefixed
cheap locals are intra-routine branch targets and would undershoot the end
catastrophically if used as bounds. If no later label exists in the bank, the
end falls back to the bank top ($bb:FFFF) — an overshoot, which is the *safe*
direction for a fail-closed impact gate.

``resolved`` is true iff the entry PC sits **exactly** on a routine-level
label. Entries whose PC merely falls inside another routine (uncorrected +/-2
annotation drift, code embedded in a data-labeled region, retired/dead entries)
are ``resolved: false`` and still carry a best-effort containing range as a
hint; the impact tool MUST always-gate them regardless of the range. This is
stricter than "pc falls inside some label's range" on purpose: it fails closed.

Usage:
    python3 registry/gen_ranges.py [--out registry/dispatch_ranges.json]
        [--rebuild] [--check]

--rebuild : force the out-of-band assemble+link even if a proven scratch image
            already exists (normally the scratch build is reused when valid).
--check   : regenerate in memory and diff against the tracked file; exit 1 on
            drift (same convention as registry/render_registry.py --check).
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import subprocess
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # umbrella ff4/
UPSTREAM = ROOT / "ff4-port" / "upstream"
BUILD = HERE / ".ranges-build"  # gitignored scratch (see .ranges-build/.gitignore)
DEFAULT_STATE = HERE / "dispatch_state.jsonl"
DEFAULT_OUT = HERE / "dispatch_ranges.json"

ROM_CRC32 = "CAA15E97"
TRACKED_ROM = UPSTREAM / "rom" / "ff4-jp1.sfc"
LNK = UPSTREAM / "ff4-jp.lnk"
MODULES = ["field", "menu", "btlgfx", "battle", "sound", "cutscene"]
# jp1 ASMFLAGS, from ff4-port/upstream/Makefile (target ff4-jp1).
JP1_DEFINES = ["-D", "BUGFIX_WORLD_BATTLE=1", "-D", "ROM_VERSION=1"]
# The SNES internal-header checksum/complement pair. These 4 bytes are the only
# ones ld65 cannot reproduce (they are computed post-link); everything else must
# match the tracked ROM byte-for-byte.
CHECKSUM_OFFSETS = range(0x7FDC, 0x7FE0)

DBG = BUILD / "ff4-jp1.dbg"
SCRATCH_ROM = BUILD / "ff4-jp1.sfc"


# --------------------------------------------------------------------------
# LoROM address helpers
# --------------------------------------------------------------------------
def snes_str(linear: int) -> str:
    """Linear bank:addr int -> 6-hex 'bbaaaa' (matches dispatch_state 'pc')."""
    return f"{linear:06X}"


def file_offset(linear: int) -> int:
    """LoROM SNES address -> flat .sfc file offset. Valid for the ROM window
    (addr >= 0x8000); every dispatch entry and its same-bank bounds live there."""
    bank = (linear >> 16) & 0x7F
    addr = linear & 0xFFFF
    return (bank << 15) | (addr & 0x7FFF)


# --------------------------------------------------------------------------
# Out-of-band build + proof
# --------------------------------------------------------------------------
def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(f"error: command failed ({' '.join(cmd)}):\n{proc.stderr}\n")
        raise SystemExit(3)


def _scratch_image_is_proven() -> bool:
    if not (DBG.is_file() and SCRATCH_ROM.is_file() and TRACKED_ROM.is_file()):
        return False
    return (zlib.crc32(SCRATCH_ROM.read_bytes()) & 0xFFFFFFFF) == int(ROM_CRC32, 16)


def build_labels(rebuild: bool = False) -> str:
    """Assemble (-g) + link (--dbgfile) out-of-band, prove against the tracked
    ROM, and leave the .dbg in the scratch dir. Returns a provenance string.
    Idempotent: a previously-proven scratch image is reused unless rebuild."""
    if not TRACKED_ROM.is_file():
        sys.stderr.write(f"error: tracked ROM not found: {TRACKED_ROM}\n")
        raise SystemExit(2)
    for tool in ("ca65", "ld65"):
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            sys.stderr.write(f"error: {tool} not found on PATH (cc65 suite required)\n")
            raise SystemExit(2)

    if not (rebuild or _scratch_image_is_proven()):
        rebuild = True

    if rebuild:
        obj_dir = BUILD / "obj"
        obj_dir.mkdir(parents=True, exist_ok=True)
        objs = []
        for m in MODULES:
            out = obj_dir / f"{m}_jp1.o"
            _run(["ca65", "-g", *JP1_DEFINES, "-I", "../include", f"{m}.asm",
                  "-o", str(out)], cwd=UPSTREAM / m)
            objs.append(str(out))
        _run(["ld65", "--dbgfile", str(DBG), "-o", str(SCRATCH_ROM),
              "-C", str(LNK), *objs], cwd=UPSTREAM)
        _prove_rom()

    upstream_commit = _upstream_commit()
    return (f"ld65 --dbgfile relink of ff4-port/upstream@{upstream_commit} "
            f"(ca65 -g, jp1 flags); labels = non-@ 'lab' symbols; "
            f"proven byte-identical to rom/ff4-jp1.sfc modulo the header checksum")


def _prove_rom() -> None:
    """Assert the relinked image matches the tracked ROM everywhere except the
    header checksum bytes, then copy those 4 bytes so CRC32 == CAA15E97."""
    tracked = bytearray(TRACKED_ROM.read_bytes())
    built = bytearray(SCRATCH_ROM.read_bytes())
    if len(built) != len(tracked):
        sys.stderr.write(f"error: relinked ROM size {len(built)} != tracked {len(tracked)}\n")
        raise SystemExit(3)
    diffs = [i for i in range(len(tracked)) if tracked[i] != built[i]]
    stray = [i for i in diffs if i not in CHECKSUM_OFFSETS]
    if stray:
        sys.stderr.write(
            f"error: relinked ROM differs from the true ROM at {len(stray)} "
            f"non-checksum byte(s) (first: {stray[:8]}) — labels are NOT proven, "
            f"refusing to emit ranges\n")
        raise SystemExit(3)
    for i in CHECKSUM_OFFSETS:
        built[i] = tracked[i]
    SCRATCH_ROM.write_bytes(built)
    crc = f"{zlib.crc32(built) & 0xFFFFFFFF:08X}"
    if crc != ROM_CRC32:
        sys.stderr.write(f"error: proven ROM CRC32 {crc} != expected {ROM_CRC32}\n")
        raise SystemExit(3)


def _upstream_commit() -> str:
    proc = subprocess.run(["git", "-C", str(UPSTREAM), "rev-parse", "--short=12", "HEAD"],
                          capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


# --------------------------------------------------------------------------
# Label parsing
# --------------------------------------------------------------------------
def _dbg_field(line: str, key: str) -> str | None:
    m = re.search(rf'\b{key}=("([^"]*)"|[^,\s]+)', line)
    if not m:
        return None
    return m.group(2) if m.group(2) is not None else m.group(1)


def parse_labels(dbg_path: Path) -> dict[int, list[str]]:
    """Return {linear_addr: [names]} for every routine-level (non-@) 'lab'
    symbol in the ROM window (addr >= 0x8000)."""
    labels: dict[int, list[str]] = {}
    with dbg_path.open() as fh:
        for line in fh:
            if not line.startswith("sym"):
                continue
            if _dbg_field(line, "type") != "lab":
                continue
            name = _dbg_field(line, "name")
            val = _dbg_field(line, "val")
            if not name or not val or not val.startswith("0x") or name.startswith("@"):
                continue
            addr = int(val, 16)
            if (addr & 0xFFFF) < 0x8000:  # ROM window only
                continue
            labels.setdefault(addr, []).append(name)
    return labels


# --------------------------------------------------------------------------
# Range computation
# --------------------------------------------------------------------------
def _next_bound(addrs: list[int], pc: int) -> int:
    """End address for a routine entered at pc: (next same-bank label - 1), or
    the bank top if pc is the last labeled thing in its bank (safe overshoot)."""
    bank = pc >> 16
    i = bisect.bisect_right(addrs, pc)
    while i < len(addrs) and (addrs[i] >> 16) == bank:
        return addrs[i] - 1
    # no later label in this bank
    return (bank << 16) | 0xFFFF


def _containing(addrs: list[int], pc: int) -> int | None:
    """Nearest same-bank label at or before pc, if any."""
    bank = pc >> 16
    i = bisect.bisect_right(addrs, pc) - 1
    if i >= 0 and (addrs[i] >> 16) == bank:
        return addrs[i]
    return None


def compute_entry(rec: dict, labels: dict[int, list[str]], addrs: list[int]) -> dict:
    pc = int(rec["pc"], 16)
    out = {
        "id": rec["id"],
        "pc": rec["pc"].upper(),
        "name": rec["name"],
        "level": rec["level"],
        "start": None,
        "end": None,
        "file_start": None,
        "file_end": None,
        "resolved": False,
        "source_label": None,
    }
    if pc in labels:  # exact hit on a routine-level label
        end = _next_bound(addrs, pc)
        out.update(
            start=snes_str(pc),
            end=snes_str(end),
            file_start=file_offset(pc),
            file_end=file_offset(end),
            resolved=True,
            source_label="/".join(labels[pc]),
        )
        return out
    # Not on a label: best-effort containing range, always-gated (resolved=False).
    host = _containing(addrs, pc)
    if host is not None:
        end = _next_bound(addrs, host)
        if pc <= end:  # pc physically falls inside the host routine
            out.update(
                start=snes_str(host),
                end=snes_str(end),
                file_start=file_offset(host),
                file_end=file_offset(end),
                resolved=False,
                source_label=f"{'/'.join(labels[host])} (containing; pc not on a label)",
            )
    return out


def generate(state_path: Path, rebuild: bool) -> dict:
    source = build_labels(rebuild=rebuild)
    labels = parse_labels(DBG)
    addrs = sorted(labels)
    records = [json.loads(l) for l in state_path.read_text().splitlines() if l.strip()]
    entries = [compute_entry(r, labels, addrs) for r in records]
    entries.sort(key=lambda e: e["pc"])  # deterministic, diff-stable
    return {
        "generated_by": "registry/gen_ranges.py",
        "source": source,
        "rom_crc32": ROM_CRC32,
        "slop": 4,  # +/-4-byte tolerance the impact tool may apply per bound
        "entries": entries,
    }


def _dump(doc: dict) -> str:
    return json.dumps(doc, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--rebuild", action="store_true",
                    help="force the out-of-band assemble+link even if a proven "
                         "scratch image already exists")
    ap.add_argument("--check", action="store_true",
                    help="regenerate in memory and diff against the tracked file; "
                         "exit 1 on drift")
    args = ap.parse_args(argv)

    if not args.state.is_file():
        sys.stderr.write(f"error: state file not found: {args.state}\n")
        return 2

    doc = generate(args.state, rebuild=args.rebuild)
    rendered = _dump(doc)

    if args.check:
        if not args.out.is_file():
            sys.stderr.write(f"drift: {args.out} does not exist\n")
            return 1
        if rendered != args.out.read_text():
            sys.stderr.write(f"drift: {args.out} does not match a fresh generation\n")
            return 1
        n = len(doc["entries"])
        r = sum(1 for e in doc["entries"] if e["resolved"])
        print(f"dispatch_ranges.json up to date ({n} entries, {r} resolved)")
        return 0

    args.out.write_text(rendered)
    n = len(doc["entries"])
    r = sum(1 for e in doc["entries"] if e["resolved"])
    print(f"wrote {args.out} ({n} entries, {r} resolved, {n - r} unresolved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
