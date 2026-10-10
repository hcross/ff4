#!/usr/bin/env python3
"""check_dead_entries — find dispatch-table entries that can never fire.

A dispatch entry only runs when the 65816 executes a JSR/JSL whose target is
exactly the entry's PC (cpu.c hooks opcodes 0x20/0x22). An entry keyed on the
wrong address is silently dead: the routine keeps running interpreted, its
native port (and whatever level the registry credits it) never executes in
game. Found 2026-10-10 on D12EE35 TfrInvertPal_c: $12:EE35 is $FF padding;
the real routine is $00:EE37 (off-by-2 annotation), called once by
`JSR $EE37` at $00:92D1.

Evidence per entry (stripped C comments first, cf. AGENTS.md §B.5):
  rom      first bytes at the PC (all $FF / all $00 = padding)
  static   JSR abs from the same bank (mirrors folded) + JSL long, anywhere
  dynamic  hits recorded by registry/check_entry_state.py (entry_state.json)
  near     a static caller target at PC±2 (the off-by-2 class)

Verdict:
  live          dynamic hits > 0
  native_callee no hook can fire it, but a ported C parent calls it by name
                (jump-table targets: jsr/jmp (abs,x) are NOT hooked by cpu.c)
  static_only   callers exist in ROM, not exercised by the fixtures
  DEAD          no static caller, no hit (indirect-call targets land here too:
                check `near` and the asm before retiring)
  DEAD_PADDING  DEAD and the PC holds padding bytes — certainly unreachable

Usage: python3 registry/check_dead_entries.py  -> registry/DEAD_ENTRIES.md
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
UMBRELLA = HERE.parent
ROM = UMBRELLA / "ff4-port" / "upstream" / "rom" / "ff4-jp1.sfc"
TABLE = UMBRELLA / "ff4-gnw" / "dispatch_all.c"
ENTRY = HERE / "entry_state.json"

_ENTRY_RE = re.compile(r"\{\s*0x([0-9A-Fa-f]{6})\s*,\s*(\w+)\s*\}")


def strip_c_comments(s: str) -> str:
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", s)


def lorom_off(pc: int) -> int | None:
    bank, addr = (pc >> 16) & 0x7F, pc & 0xFFFF
    if addr < 0x8000:
        return None
    return bank * 0x8000 + (addr - 0x8000)


def main() -> int:
    rom = ROM.read_bytes()
    nbanks = len(rom) // 0x8000
    entries = [(int(pc, 16), fn) for pc, fn in _ENTRY_RE.findall(strip_c_comments(TABLE.read_text()))]
    hits = {}
    if ENTRY.is_file():
        for r in json.loads(ENTRY.read_text()):
            hits[r["id"]] = sum(o["hits"] for o in r["observed"])

    # Index every JSR abs (by bank) and JSL long target in the ROM. Opcode
    # scanning over data yields false positives, never false negatives for
    # real direct calls -- good enough to prove "no direct caller".
    jsr = {}   # (bank, addr16) -> count
    jsl = {}   # pc24 (bank folded) -> count
    for b in range(nbanks):
        chunk = rom[b * 0x8000:(b + 1) * 0x8000]
        for i in range(len(chunk) - 3):
            op = chunk[i]
            if op == 0x20:
                t = chunk[i + 1] | (chunk[i + 2] << 8)
                if t >= 0x8000:
                    jsr[(b, t)] = jsr.get((b, t), 0) + 1
            elif op == 0x22:
                t = chunk[i + 1] | (chunk[i + 2] << 8) | ((chunk[i + 3] & 0x7F) << 16)
                if (t & 0xFFFF) >= 0x8000:
                    jsl[t] = jsl.get(t, 0) + 1

    # Native call graph: a routine reached only through a jump table
    # (jsr (abs,x) / jmp (abs,x) -- NOT hooked by cpu.c) still runs natively
    # when an already-ported C parent calls it by name.
    gnw = UMBRELLA / "ff4-gnw"
    corpus = {}
    for f in gnw.rglob("*.c"):
        if "snes" in f.parts or f.name == "dispatch_all.c":
            continue
        corpus[f] = strip_c_comments(f.read_text(errors="replace"))

    def c_callers(fn: str) -> list[str]:
        call = re.compile(rf"\b{re.escape(fn)}\s*\(\s*snes")
        defn = re.compile(rf"\bvoid\s+{re.escape(fn)}\s*\(")
        out = []
        for f, txt in corpus.items():
            n = len(call.findall(txt)) - len(defn.findall(txt))
            if n > 0:
                out.append(f.stem)
        return out

    rows = []
    for pc, fn in entries:
        did = f"D{pc:06X}"
        off = lorom_off(pc)
        head = rom[off:off + 6] if off is not None and off + 6 <= len(rom) else b""
        padding = bool(head) and (set(head) <= {0xFF} or set(head) <= {0x00})
        b, a = (pc >> 16) & 0x7F, pc & 0xFFFF
        static = jsr.get((b, a), 0) + jsl.get((b << 16) | a, 0)
        near = [f"{d:+d}" for d in (-2, 2)
                if jsr.get((b, a + d), 0) + jsl.get((b << 16) | (a + d), 0)]
        dyn = hits.get(did, 0)
        cc = c_callers(fn)
        if dyn:
            v = "live"
        elif static:
            v = "static_only"
        elif cc:
            v = "native_callee"
        else:
            v = "DEAD_PADDING" if padding else "DEAD"
        rows.append({"id": did, "fn": fn, "verdict": v, "static": static, "hits": dyn,
                     "near": near, "rom": head.hex(" "), "c_callers": cc})

    order = {"DEAD_PADDING": 0, "DEAD": 1, "native_callee": 2, "static_only": 3, "live": 4}
    rows.sort(key=lambda r: (order[r["verdict"]], r["id"]))
    counts = {k: sum(1 for r in rows if r["verdict"] == k) for k in order}
    lines = [
        "<!-- GENERATED by registry/check_dead_entries.py - do not edit by hand. -->",
        "# Dispatch entries that can never fire",
        "",
        "A dispatch entry runs only when a JSR/JSL targets exactly its PC. `DEAD` = no direct "
        "caller in the ROM and no hit on any fixture (an indirect-call target also lands here — "
        "read the asm before retiring); `DEAD_PADDING` = the PC holds padding bytes, certainly "
        "unreachable. `near` = a direct caller targets PC±2 (the off-by-2 annotation class: the "
        "entry should move there). Dynamic hits come from `check_entry_state.py`.",
        "",
        "| Verdict | Count |", "|---|---|",
        *[f"| {k} | {counts[k]} |" for k in order],
        "",
        "| ID | Function | Verdict | Static callers | Fixture hits | Caller at PC± | C callers | ROM bytes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r["verdict"] == "live":
            continue
        lines.append(f"| {r['id']} | `{r['fn']}` | {r['verdict']} | {r['static']} | {r['hits']} | "
                     f"{' '.join(r['near'])} | {', '.join(r['c_callers'][:3])} | `{r['rom']}` |")
    (HERE / "DEAD_ENTRIES.md").write_text("\n".join(lines) + "\n")
    print(" ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
