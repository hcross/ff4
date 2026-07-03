#!/usr/bin/env python3
"""registry_promote — the sanctioned write path for dispatch_state.jsonl.

A Sonnet-class agent (or anyone) should never hand-edit
registry/dispatch_state.jsonl or DISPATCH_REGISTRY.md's Table 1 directly.
This is the only writer: it validates that a level transition is
monotonic (or an explicit, logged exception) and that evidence for it
actually exists on disk before recording it, then re-renders
DISPATCH_REGISTRY.md so the two never drift apart again.

Usage:
    python registry/registry_promote.py D0081F4 --to L2 \\
        --evidence ../ff4-port/translator/runs/some_run.jsonl \\
        --note "fuzzed spike, 0 fails"

    # Off-scale / categorical levels (EXCL, DELEG, RETIRED, L0) always
    # allowed regardless of the current level, but still require --note:
    python registry/registry_promote.py D038085 --to RETIRED \\
        --note "BLOCKING animation (Wait*), must remain interpreted"

    # Demote (e.g. a lint/oracle run disproves a prior L2 credit) requires
    # --allow-demote to be explicit about it:
    python registry/registry_promote.py D04861E --to L1 --allow-demote \\
        --note "false-L2: writes ram[0x2140..0x2143] instead of apu->inPorts"
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_STATE = HERE / "dispatch_state.jsonl"

SEQUENCE = ["L0", "L1", "L2", "L3"]           # monotonic ladder
CATEGORICAL = {"EXCL", "DELEG", "RETIRED"}    # off-scale, always allowed


def load_records(state_path: Path) -> list[dict]:
    records = []
    with state_path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_records(state_path: Path, records: list[dict]) -> None:
    with state_path.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def validate_transition(current: str, target: str, allow_demote: bool) -> tuple[bool, str]:
    if target in CATEGORICAL or current in CATEGORICAL:
        return True, ""
    if current not in SEQUENCE or target not in SEQUENCE:
        return True, ""  # unknown level string — don't block, just proceed
    cur_i, tgt_i = SEQUENCE.index(current), SEQUENCE.index(target)
    if tgt_i == cur_i:
        return False, f"{current} -> {target} is a no-op"
    if tgt_i > cur_i + 1:
        return False, (f"{current} -> {target} skips a level "
                        f"(promote one step at a time: {SEQUENCE[cur_i+1]} first)")
    if tgt_i < cur_i and not allow_demote:
        return False, (f"{current} -> {target} is a demotion — pass --allow-demote "
                        "if this is a deliberate correction (e.g. a false-L2 found)")
    return True, ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dispatch_id", help="e.g. D0081F4")
    ap.add_argument("--to", required=True, help="target level: L0, L1, L2, L3, EXCL, DELEG, RETIRED")
    ap.add_argument("--evidence", type=Path,
                     help="path to a file proving the transition (spike JSONL, oracle "
                          "--json output, ...). Required for L1->L2 and L2->L3; optional "
                          "otherwise but recorded in notes if given.")
    ap.add_argument("--note", required=True, help="short human-readable justification")
    ap.add_argument("--allow-demote", action="store_true",
                     help="required to move backward in the L0-L3 ladder")
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--no-render", action="store_true",
                     help="skip auto-invoking render_registry.py after a successful write")
    args = ap.parse_args(argv)

    target = args.to.strip().upper()
    if target not in SEQUENCE and target not in CATEGORICAL:
        sys.stderr.write(f"error: unknown target level {target!r} "
                          f"(choices: {SEQUENCE + sorted(CATEGORICAL)})\n")
        return 2

    if not args.state.is_file():
        sys.stderr.write(f"error: state file not found: {args.state}\n")
        return 2
    records = load_records(args.state)
    rec = next((r for r in records if r["id"] == args.dispatch_id), None)
    if rec is None:
        sys.stderr.write(f"error: no dispatch with id {args.dispatch_id!r} in {args.state}\n")
        return 1

    current = rec["level"]
    ok, why = validate_transition(current, target, args.allow_demote)
    if not ok:
        sys.stderr.write(f"error: {why}\n")
        return 1

    needs_evidence = (current, target) in (("L1", "L2"), ("L2", "L3"))
    if needs_evidence:
        if args.evidence is None:
            sys.stderr.write(f"error: {current} -> {target} requires --evidence "
                              "(a spike run for L1->L2, an oracle run for L2->L3)\n")
            return 1
        if not args.evidence.is_file():
            sys.stderr.write(f"error: evidence file not found: {args.evidence}\n")
            return 1
        if args.evidence.stat().st_size == 0:
            sys.stderr.write(f"error: evidence file is empty: {args.evidence}\n")
            return 1

    today = datetime.date.today().isoformat()
    evidence_note = f" (evidence: {args.evidence})" if args.evidence else ""
    rec["level"] = target
    rec["notes"] = args.note + evidence_note
    rec["updated"] = today
    save_records(args.state, records)
    print(f"{args.dispatch_id}: {current} -> {target} ({args.note})")

    if not args.no_render:
        import subprocess
        res = subprocess.run(
            [sys.executable, str(HERE / "render_registry.py"), "--state", str(args.state)],
        )
        if res.returncode != 0:
            sys.stderr.write("warning: render_registry.py failed — DISPATCH_REGISTRY.md "
                              "was NOT updated; run it manually\n")
            return res.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
