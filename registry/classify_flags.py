#!/usr/bin/env python3
"""classify_flags — static dispatchability + DP-risk flags for every dispatch.

Populates the `flags` field of registry/dispatch_state.jsonl by statically
scanning each routine's asm (via ca65-bridge) and its ff4-gnw C body.
Read-only with respect to dispatch_all.c — this never decides what gets
dispatched, it only records what a human/agent should check before trusting
a routine's current status.

Flags:
  WAIT_BLOCKING  — asm jsr/jsl's into the Wait*/ExecBtlGfx family, or the
                   routine itself IS one of them. These block for multiple
                   frames and hang run_emulated_func's synchronous
                   single-frame execution if ever dispatched/delegated
                   (the confirmed root cause of the ExecBtlGfx combat bug).
  TAIL_JML       — the asm body's last instruction is jml/jmp (tail-jump,
                   never returns via rts/rtl) — incompatible with the
                   dispatch hook's simulated-return mechanism.
  DMA_TRIGGER    — asm stores to hMDMAEN/hHDMAEN ($420B/$420C) or a DMA
                   channel register ($43xx) — needs the manual-transfer-loop
                   treatment (Pitfall 15), not a bare register write.
  SPC_MAILBOX    — asm reads or writes hAPUIO0-3 ($2140-$2143) — driving the
                   SPC700 handshake; a no-op stub here can hang the audio
                   boot sequence (see gen_dispatch.py SKIPPED_ROUTINES).
  DP_SENSITIVE   — the ff4-gnw C body accesses WRAM via bare `ram[N]` /
                   `write16(ram, N, ...)` for small N (< 0x1000, the
                   direct-page-scale range) WITHOUT ever computing the
                   address relative to `snes->cpu->dp`. This is a
                   MECHANICAL PROXY, not a verdict: it only means "if this
                   routine's real entry D is non-zero, this port reads/
                   writes the wrong address" (the exact bug fixed in
                   CheckMenu_c/_00883d_c/_00885e_c). It fires for entire
                   modules whose true D is unverified per-routine — see
                   CONVENTIONS.md. A DP_SENSITIVE flag is a "verify before
                   trusting" signal, not a confirmed bug.

Usage:
    python registry/classify_flags.py [--state dispatch_state.jsonl]
        [--ffgnw ../ff4-gnw] [--upstream ../ff4-port/upstream]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_STATE = HERE / "dispatch_state.jsonl"
DEFAULT_FFGNW = ROOT / "ff4-gnw"
DEFAULT_UPSTREAM = ROOT / "ff4-port" / "upstream"
BRIDGE_BIN = ROOT / "ff4-port" / "ca65-bridge" / ".venv" / "bin" / "ca65-bridge"

# Modules with at least one CONFIRMED non-zero direct-page call context
# (see CONVENTIONS.md) — DP_SENSITIVE only fires here, since flagging every
# module (including battle, where DP=0 is well-established and unchallenged)
# would be noise, not signal.
DP_RISK_MODULES = {"field", "menu"}

_WAIT_FAMILY_RE = re.compile(
    r"\b(?:jsr|jsl)\s+(Wait\w*|ExecBtlGfx\w*)\b", re.IGNORECASE
)
_HW_SYMBOL_DEF_RE = re.compile(r"^\s*(h[A-Za-z0-9_]+)\s*:=\s*\$([0-9A-Fa-f]+)", re.MULTILINE)
_STORE_OR_LOAD_OPCODE_RE = re.compile(
    r"^\s*(?:@[A-Za-z0-9_]+:\s*)?"
    r"(?:sta|stx|sty|stz|lda|ldx|ldy|inc|dec|asl|lsr|rol|ror|trb|tsb|cmp)(?:\.[bwl])?\s+"
    r"([\w$]+)",
    re.IGNORECASE | re.MULTILINE,
)
_MMIO_ASSIGN_RE = re.compile(
    r"\bram\s*\[\s*0x([0-9A-Fa-f]{1,4})\s*\]\s*=(?!=)"
    r"|\bwrite16\s*\(\s*ram\s*,\s*0x([0-9A-Fa-f]{1,4})\s*,"
)


def get_asm(func_name: str, upstream: Path) -> str:
    res = subprocess.run(
        [str(BRIDGE_BIN), "--root", str(upstream), "get-asm", func_name],
        capture_output=True, text=True,
    )
    return res.stdout if res.returncode == 0 else ""


def hw_symbols(upstream: Path) -> dict[str, int]:
    inc = upstream / "include" / "hardware.inc"
    if not inc.is_file():
        return {}
    return {name: int(addr, 16) for name, addr in _HW_SYMBOL_DEF_RE.findall(inc.read_text())}


def hw_addrs_touched(asm_text: str, syms: dict[str, int]) -> set[int]:
    hits = set()
    for m in _STORE_OR_LOAD_OPCODE_RE.finditer(asm_text):
        operand = m.group(1)
        addr = None
        if operand in syms:
            addr = syms[operand]
        elif operand.startswith("$"):
            try:
                addr = int(operand[1:], 16)
            except ValueError:
                addr = None
        if addr is not None:
            hits.add(addr)
    return hits


def last_instruction(asm_text: str) -> str:
    lines = [ln.strip() for ln in asm_text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    return lines[-1].lower() if lines else ""


def classify_one(name: str, module: str, ffgnw: Path, upstream: Path, syms: dict[str, int]) -> list[str]:
    flags = []
    # ca65-bridge resolves asm LABELS, which never carry the C '_c' suffix
    # generate_spike.py/gen_dispatch.py append for the dispatched function name.
    asm_label = name[:-2] if name.endswith("_c") else name
    asm = get_asm(asm_label, upstream)

    if asm:
        if _WAIT_FAMILY_RE.search(asm) or asm_label.startswith("Wait") or asm_label.startswith("ExecBtlGfx"):
            flags.append("WAIT_BLOCKING")
        last = last_instruction(asm)
        if last.startswith("jml") or (last.startswith("jmp") and "(" not in last):
            flags.append("TAIL_JML")
        touched = hw_addrs_touched(asm, syms)
        if any(a in (0x420B, 0x420C) or 0x4300 <= a <= 0x43FF for a in touched):
            flags.append("DMA_TRIGGER")
        if any(0x2140 <= a <= 0x2143 for a in touched):
            flags.append("SPC_MAILBOX")

    if module in DP_RISK_MODULES:
        base = name[:-2] if name.endswith("_c") else name
        cfile = ffgnw / module / f"{base}.c"
        if cfile.is_file():
            text = cfile.read_text(errors="replace")
            no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
            no_line = re.sub(r"//[^\n]*", "", no_block)
            uses_dynamic_dp = "cpu->dp" in no_line
            has_small_offset = False
            for m in _MMIO_ASSIGN_RE.finditer(no_line):
                addr = int(m.group(1) or m.group(2), 16)
                if addr < 0x1000:
                    has_small_offset = True
                    break
            if not uses_dynamic_dp and has_small_offset:
                flags.append("DP_SENSITIVE")

    return flags


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--ffgnw", type=Path, default=DEFAULT_FFGNW)
    ap.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    args = ap.parse_args(argv)

    if not args.state.is_file():
        sys.stderr.write(f"error: state file not found: {args.state}\n")
        return 2

    records = []
    with args.state.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    syms = hw_symbols(args.upstream)
    tally: dict[str, int] = {}
    for r in records:
        if r["level"] == "RETIRED":
            continue
        flags = classify_one(r["name"], r["module"], args.ffgnw, args.upstream, syms)
        r["flags"] = flags
        for f in flags:
            tally[f] = tally.get(f, 0) + 1

    with args.state.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")

    print(f"classified {len(records)} records")
    for f, n in sorted(tally.items()):
        print(f"  {f}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
