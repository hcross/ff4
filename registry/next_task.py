#!/usr/bin/env python3
"""next_task — derive the next unit of work from dispatch_state.jsonl.

Removes the cold-start cost the original audit identified: picking the
correct next dispatch required joining DISPATCH_REGISTRY.md + BACKLOG.md +
REPRISE.md + miss_profiler output + MemPalace mentally. This reads only
the registry (fast, no subprocess calls to ca65-bridge or the desktop
tools) and buckets candidates by what's actually actionable next,
highest-confidence / lowest-risk first.

Buckets (in priority order):
  1. dp_verify      — DP_SENSITIVE-flagged L2 field routines: they read or
                       write low WRAM without dp-relative addressing, and
                       field's true D is confirmed non-uniform (D=$0600 for
                       the NMI/FieldMain-loop context, D=0 elsewhere) — see
                       ff4-gnw/CONVENTIONS.md. NOT the menu module: its 8
                       dispatched files are thin delegates with zero direct
                       WRAM access, verified harmless despite also lacking
                       dynamic dp (see CONVENTIONS.md's corrected finding).
  2. no_contract     — L1 with "no CONTRACT block": write one, then spike.
  3. fixable_l1      — L1 with a notes hint of a mechanical, closeable gap
                       (compile_error / parser_error / spike does not
                       compile) — re-attempt via generate_spike.py.
  4. custom_spike    — L1 "non-standalone body (bundled btlgfx)" or
                       otherwise requiring a hand-written spike (T3 in
                       ESCALATION.md if the mask/region design isn't obvious).
  5. l3_candidate    — L2, no WAIT_BLOCKING/DMA_TRIGGER/SPC_MAILBOX/
                       DP_SENSITIVE flag: a clean oracle-validation
                       candidate (still needs a fixture that exercises it —
                       not selected here).
  6. flagged_l2      — L2 with a DMA_TRIGGER/SPC_MAILBOX/DP_SENSITIVE flag,
                       not yet demoted or promoted to L3: worth an oracle
                       check before trusting further (the ExecInterrupt_c
                       class).

Usage:
    python registry/next_task.py [--bucket NAME] [--limit N] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_STATE = HERE / "dispatch_state.jsonl"

BUCKET_ORDER = ["dp_verify", "no_contract", "fixable_l1", "custom_spike",
                "l3_candidate", "flagged_l2"]

_FIXABLE_HINTS = ("compile_error", "does not compile", "parser_error", "run_hang")


def load_records(state_path: Path) -> list[dict]:
    records = []
    with state_path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def bucket_of(r: dict) -> str | None:
    level = r["level"]
    flags = r.get("flags", [])
    notes = r.get("notes", "").lower()

    if level == "L2" and "DP_SENSITIVE" in flags:
        return "dp_verify"
    if level != "L1" and level != "L2":
        return None  # L0/L3/EXCL/DELEG/RETIRED are not "next work" candidates here
    if level == "L1":
        if "no contract" in notes:
            return "no_contract"
        if any(h in notes for h in _FIXABLE_HINTS):
            return "fixable_l1"
        if "non-standalone" in notes or "bundled" in notes:
            return "custom_spike"
        return "fixable_l1"  # default bucket for any other L1
    if level == "L2":
        if any(f in flags for f in ("DMA_TRIGGER", "SPC_MAILBOX", "DP_SENSITIVE")):
            return "flagged_l2"
        if not flags:
            return "l3_candidate"
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--bucket", choices=BUCKET_ORDER, help="show only this bucket")
    ap.add_argument("--limit", type=int, default=5, help="max entries shown per bucket")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not args.state.is_file():
        sys.stderr.write(f"error: state file not found: {args.state}\n")
        return 2

    records = load_records(args.state)
    buckets: dict[str, list[dict]] = {b: [] for b in BUCKET_ORDER}
    for r in records:
        b = bucket_of(r)
        if b:
            buckets[b].append(r)

    if args.bucket:
        order = [args.bucket]
    else:
        order = BUCKET_ORDER

    if args.json:
        out = {b: [{"id": r["id"], "name": r["name"], "module": r["module"],
                     "level": r["level"], "flags": r.get("flags", []),
                     "notes": r["notes"]} for r in buckets[b][:args.limit]]
               for b in order}
        print(json.dumps(out, indent=2))
        return 0

    total = sum(len(buckets[b]) for b in order)
    if total == 0:
        print("No actionable candidates found in the requested bucket(s).")
        return 0
    for b in order:
        items = buckets[b]
        if not items:
            continue
        print(f"\n=== {b} ({len(items)} total, showing {min(len(items), args.limit)}) ===")
        for r in items[:args.limit]:
            flags = f" [{','.join(r['flags'])}]" if r.get("flags") else ""
            print(f"  {r['id']}  {r['name']}  ({r['module']}, {r['level']}){flags}")
            print(f"      {r['notes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
