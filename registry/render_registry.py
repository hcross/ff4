#!/usr/bin/env python3
"""render_registry — regenerate DISPATCH_REGISTRY.md's distribution line and
Table 1 from registry/dispatch_state.jsonl.

Once this has run once, DISPATCH_REGISTRY.md carries
<!-- REGISTRY:...:START/END --> markers around the generated distribution
line and Table 1; every subsequent run replaces only the content between
those markers, leaving all prose (ADRs, lessons, Table 2/3, footer notes)
untouched. Table 1 rows are sorted by PC (ascending), matching the
document's existing convention.

Usage:
    python registry/render_registry.py [--registry DISPATCH_REGISTRY.md]
        [--state registry/dispatch_state.jsonl] [--check]

--check: render into memory and diff against the file on disk; exit 1 if
they differ (drift check, does not write).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_REGISTRY_MD = ROOT / "DISPATCH_REGISTRY.md"
DEFAULT_STATE = HERE / "dispatch_state.jsonl"

DIST_START = "<!-- REGISTRY:DISTRIBUTION:START -->"
DIST_END = "<!-- REGISTRY:DISTRIBUTION:END -->"
TABLE_START = "<!-- REGISTRY:TABLE1:START -->"
TABLE_END = "<!-- REGISTRY:TABLE1:END -->"

_TABLE1_HEADER_RE = re.compile(r"^\|\s*ID\s*\|\s*SNES Address\s*\|")
_ROW_RE = re.compile(r"^\|\s*`D[0-9A-Fa-f]{6}`\s*\|")
_OLD_DIST_RE = re.compile(r"^\*\*Distribution\*\*")


def load_records(state_path: Path) -> list[dict]:
    records = []
    with state_path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def render_distribution(records: list[dict]) -> str:
    by_level: dict[str, int] = {}
    for r in records:
        by_level[r["level"]] = by_level.get(r["level"], 0) + 1
    order = ["L0", "L1", "L2", "L3", "EXCL", "DELEG"]
    parts = [f"{lvl}={by_level[lvl]}" for lvl in order if lvl in by_level]
    extra = [f"{lvl}={n}" for lvl, n in sorted(by_level.items()) if lvl not in order]
    total = sum(n for lvl, n in by_level.items() if lvl not in ("RETIRED",))
    line1 = (DIST_START + "\n"
              f"**Distribution** (generated from `registry/dispatch_state.jsonl` — "
              f"do not hand-edit; edit the JSONL via `registry/registry_promote.py` "
              f"and re-run `python registry/render_registry.py`): "
              + " · ".join(parts + extra) + f" (total {total}).\n"
              + DIST_END)
    return line1


def render_table1(records: list[dict]) -> str:
    header = "| ID | SNES Address | C Routine | Domain | Level | Proof / notes |"
    sep = "|----|--------------|-----------|--------|-------|---------------|"
    rows = []
    for r in sorted(records, key=lambda r: r["pc"]):
        rows.append(
            f"| `{r['id']}` | {r['addr_display']} | `{r['name']}` | {r['module']} | "
            f"{r['level']} | {r['notes']} |"
        )
    return "\n".join([TABLE_START, header, sep] + rows + [TABLE_END])


def apply_markers(text: str, records: list[dict]) -> str:
    dist_block = render_distribution(records)
    table_block = render_table1(records)

    if DIST_START in text and DIST_END in text:
        text = re.sub(
            re.escape(DIST_START) + r".*?" + re.escape(DIST_END),
            dist_block, text, flags=re.DOTALL, count=1,
        )
    else:
        # Bootstrap: replace the old hand-written distribution line + its
        # continuation lines (everything up to the next blank-ish anchor —
        # the stable "`ExecBtlGfx` (D038085) REMOVED" prose line) with the
        # marked block.
        lines = text.splitlines()
        start = next((i for i, ln in enumerate(lines) if _OLD_DIST_RE.match(ln)), None)
        if start is None:
            sys.stderr.write("error: could not find the old **Distribution** line to replace\n")
            sys.exit(1)
        end = start + 1
        while end < len(lines) and not lines[end].startswith("`ExecBtlGfx`"):
            end += 1
        lines[start:end] = dist_block.splitlines()
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

    if TABLE_START in text and TABLE_END in text:
        text = re.sub(
            re.escape(TABLE_START) + r".*?" + re.escape(TABLE_END),
            table_block, text, flags=re.DOTALL, count=1,
        )
    else:
        lines = text.splitlines()
        start = next((i for i, ln in enumerate(lines) if _TABLE1_HEADER_RE.match(ln)), None)
        if start is None:
            sys.stderr.write("error: could not find the Table 1 header to replace\n")
            sys.exit(1)
        end = start + 2  # skip header + separator
        while end < len(lines) and _ROW_RE.match(lines[end]):
            end += 1
        lines[start:end] = table_block.splitlines()
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_MD)
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--check", action="store_true",
                     help="diff only, do not write; exit 1 on drift")
    args = ap.parse_args(argv)

    if not args.state.is_file():
        sys.stderr.write(f"error: state file not found: {args.state}\n")
        return 2
    if not args.registry.is_file():
        sys.stderr.write(f"error: registry not found: {args.registry}\n")
        return 2

    records = load_records(args.state)
    original = args.registry.read_text()
    rendered = apply_markers(original, records)

    if args.check:
        if rendered != original:
            sys.stderr.write(f"drift: {args.registry} does not match {args.state}\n")
            return 1
        print("registry is up to date")
        return 0

    if rendered != original:
        args.registry.write_text(rendered)
        print(f"updated {args.registry}")
    else:
        print(f"{args.registry} already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
