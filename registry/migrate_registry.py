#!/usr/bin/env python3
"""migrate_registry — one-shot parser: DISPATCH_REGISTRY.md Table 1 -> dispatch_state.jsonl.

This is the bootstrap for the machine-readable registry (Wave 1 of the
ff4-wave0/1-accel plan): DISPATCH_REGISTRY.md's Table 1 has been
hand-maintained markdown, which drifted (its own summary line disagreed
with its own rows — see the 2026-07-03 fix). From here on,
registry/dispatch_state.jsonl is the source of truth; DISPATCH_REGISTRY.md
Table 1 is regenerated from it by render_registry.py.

Safe to re-run: it always re-parses the current Table 1 fresh. Once the
registry is the live source of truth (i.e. DISPATCH_REGISTRY.md carries the
GENERATED banner from render_registry.py), do not run this again — hand
edits to dispatch_state.jsonl or registry_promote.py are the only writers.

Usage:
    python registry/migrate_registry.py [--registry DISPATCH_REGISTRY.md]
        [--out registry/dispatch_state.jsonl] [--check]

--check: parse and validate only (cross-check the ID/PC set against
ff4-gnw/dispatch_all.c), do not write the JSONL.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # umbrella ff4/
DEFAULT_REGISTRY_MD = ROOT / "DISPATCH_REGISTRY.md"
DEFAULT_OUT = HERE / "dispatch_state.jsonl"
DEFAULT_DISPATCH_ALL_C = ROOT / "ff4-gnw" / "dispatch_all.c"

_TABLE1_HEADER_RE = re.compile(r"^\|\s*ID\s*\|\s*SNES Address\s*\|")
_ROW_RE = re.compile(
    r"^\|\s*`(D[0-9A-Fa-f]{6})`\s*\|\s*(\$[0-9A-Fa-f]{2}:[0-9A-Fa-f]{4})\s*\|"
    r"\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$"
)


def parse_table1(md_text: str) -> list[dict]:
    lines = md_text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if _TABLE1_HEADER_RE.match(ln):
            start = i + 2  # skip the header row and the |---|---| separator
            break
    if start is None:
        sys.stderr.write("error: could not find the Table 1 header in the registry\n")
        return []

    records = []
    for ln in lines[start:]:
        m = _ROW_RE.match(ln)
        if not m:
            if ln.strip() == "" or ln.strip().startswith("|"):
                # Either a blank line (end of table) or a non-matching table
                # row (e.g. a placeholder) — either way, Table 1 has ended
                # once we hit a line that isn't blank and isn't a data row.
                if ln.strip() == "":
                    break
                continue
            break
        dispatch_id, addr_display, name, module, level, notes = m.groups()
        pc = addr_display.replace("$", "").replace(":", "").upper()
        records.append({
            "id": dispatch_id,
            "pc": pc,
            "addr_display": addr_display,
            "name": name,
            "module": module.strip(),
            "level": level.strip(),
            "notes": notes.strip(),
            "flags": [],
            "updated": None,
        })
    return records


def cross_check(records: list[dict], dispatch_all_c: Path) -> list[str]:
    """Compare the migrated ID set against the live dispatch table. Returns
    a list of human-readable warnings (empty if consistent)."""
    warnings = []
    if not dispatch_all_c.is_file():
        warnings.append(f"dispatch_all.c not found at {dispatch_all_c} — skipping cross-check")
        return warnings
    text = dispatch_all_c.read_text(errors="replace")
    code_pcs = set(m.group(1).upper() for m in re.finditer(
        r"\{\s*0x([0-9A-Fa-f]{6})\s*,", text))
    registry_pcs = set(r["pc"] for r in records if r["level"] not in ("RETIRED",))
    only_in_code = code_pcs - registry_pcs
    only_in_registry = registry_pcs - code_pcs
    if only_in_code:
        warnings.append(f"{len(only_in_code)} PC(s) in dispatch_all.c but not in the registry: "
                         + ", ".join(sorted(only_in_code)[:10])
                         + (" ..." if len(only_in_code) > 10 else ""))
    if only_in_registry:
        warnings.append(f"{len(only_in_registry)} PC(s) in the registry (non-RETIRED) but not "
                         "in dispatch_all.c: " + ", ".join(sorted(only_in_registry)[:10])
                         + (" ..." if len(only_in_registry) > 10 else ""))
    return warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_MD)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--dispatch-all-c", type=Path, default=DEFAULT_DISPATCH_ALL_C)
    ap.add_argument("--check", action="store_true",
                     help="parse and cross-check only, do not write the JSONL")
    args = ap.parse_args(argv)

    if not args.registry.is_file():
        sys.stderr.write(f"error: registry not found: {args.registry}\n")
        return 2

    records = parse_table1(args.registry.read_text())
    if not records:
        sys.stderr.write("error: parsed zero records — check the Table 1 format\n")
        return 1

    by_level: dict[str, int] = {}
    for r in records:
        by_level[r["level"]] = by_level.get(r["level"], 0) + 1
    print(f"parsed {len(records)} records from {args.registry}")
    for lvl, n in sorted(by_level.items()):
        print(f"  {lvl}: {n}")

    warnings = cross_check(records, args.dispatch_all_c)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)

    if args.check:
        return 1 if warnings else 0

    with args.out.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print(f"wrote {args.out}")
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
