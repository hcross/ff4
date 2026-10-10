#!/usr/bin/env python3
"""check_entry_state — cross-check every CONTRACT's entry_mode against the
CPU state the game actually enters the routine with.

Runs ff4-port/desktop/ff4-entry-probe over every fixture, aggregates the
observed (D, DB, m, x) tuples per dispatched PC, and compares them with the
`// CONTRACT: entry_mode: mf=, xf=, dp=, db=` line of the routine's source.
A spike replays the DECLARED state, so a wrong dp=/db= makes a green spike
meaningless (AGENTS.md golden rule 1; the DP_SENSITIVE flag of
classify_flags.py only says "verify this", this tool verifies it).

Verdicts per routine:
  ok            every observed entry matches the CONTRACT
  MISMATCH      some observed entry differs on dp/db/m/x (listed)
  multi_entry   the game enters with several distinct states (the CONTRACT
                can only describe one; the spike covers one of them)
  not_hit       no fixture exercises the routine (no evidence either way)
  no_contract   no parsable CONTRACT

Usage: python3 registry/check_entry_state.py [--frames 600] [--build]
Writes registry/ENTRY_STATE.md (generated) and prints a one-line summary.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
UMBRELLA = HERE.parent
PORT = UMBRELLA / "ff4-port"
DESKTOP = PORT / "desktop"
PROBE = DESKTOP / "ff4-entry-probe"
ROM = PORT / "upstream" / "rom" / "ff4-jp1.sfc"
FIXTURES = PORT / "fixtures"
STATE = HERE / "dispatch_state.jsonl"
FFGNW = UMBRELLA / "ff4-gnw"
MODULE_DIRS = ["battle", "field", "menu", "cutscene", "sound", "btlgfx"]

_ENTRY_RE = re.compile(r"ENTRY ([0-9A-F]{6}) dp=([0-9A-F]{4}) db=([0-9A-F]{2}) m=(\d) x=(\d) hits=(\d+)")
_MODE_RE = re.compile(r"//\s*entry_mode:\s*([^\n]+)")


def find_source(name: str) -> Path | None:
    base = name[:-2] if name.endswith("_c") else name
    for stem in (base, base + "Entry"):
        for mod in MODULE_DIRS:
            cand = FFGNW / mod / f"{stem}.c"
            if cand.is_file():
                return cand
    return None


def contract_mode(src: Path) -> dict | None:
    text = src.read_text()
    if "// CONTRACT:" not in text:
        return None
    m = _MODE_RE.search(text[text.index("// CONTRACT:"):])
    if not m:
        return None
    out = {}
    for k, v in re.findall(r"(\w+)\s*=\s*([0-9A-Fa-fx]+|true|false)", m.group(1)):
        k = k.lower()
        if k in ("mf", "xf"):
            out[k] = 1 if v.lower() == "true" else 0
        elif k in ("dp", "db"):
            out[k] = int(v, 16)
    return out


def probe(lss: Path, frames: int) -> list[tuple]:
    r = subprocess.run([str(PROBE), str(ROM), "--load", str(lss), "--frames", str(frames)],
                       capture_output=True, text=True, timeout=1800)
    return [(m[0], int(m[1], 16), int(m[2], 16), int(m[3]), int(m[4]), int(m[5]), lss.stem)
            for m in _ENTRY_RE.findall(r.stdout)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", type=int, default=600)
    ap.add_argument("--build", action="store_true", help="make ff4-entry-probe first")
    ap.add_argument("--out", type=Path, default=HERE / "ENTRY_STATE.md")
    args = ap.parse_args(argv)
    if args.build or not PROBE.is_file():
        subprocess.run(["make", "-C", str(DESKTOP), "ff4-entry-probe"], check=True,
                       capture_output=True)

    fixtures = sorted(FIXTURES.glob("*.lss"))
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = [row for rs in ex.map(lambda f: probe(f, args.frames), fixtures) for row in rs]
    seen = defaultdict(lambda: defaultdict(lambda: [0, set()]))  # pc -> (dp,db,m,x) -> [hits, fixtures]
    for pc, dp, db, m, x, hits, fx in rows:
        slot = seen[pc][(dp, db, m, x)]
        slot[0] += hits
        slot[1].add(fx)

    recs = [json.loads(l) for l in STATE.read_text().splitlines() if l.strip()]
    live = [r for r in recs if r["level"] not in ("RETIRED",)]
    results = []
    for r in live:
        src = find_source(r["name"])
        mode = contract_mode(src) if src else None
        obs = seen.get(r["pc"].upper(), {})
        res = {"id": r["id"], "name": r["name"], "level": r["level"],
               "flags": r.get("flags", []), "contract": mode,
               "observed": [{"dp": k[0], "db": k[1], "m": k[2], "x": k[3], "hits": v[0],
                             "fixtures": sorted(v[1])} for k, v in obs.items()]}
        if mode is None:
            res["verdict"] = "no_contract"
        elif not obs:
            res["verdict"] = "not_hit"
        else:
            bad = []
            for (dp, db, m, x) in obs:
                diffs = [f for f, o in (("dp", dp), ("db", db), ("mf", m), ("xf", x))
                         if f in mode and mode[f] != o]
                if diffs:
                    bad.append(diffs)
            if bad:
                res["verdict"] = "MISMATCH"
                res["mismatch_fields"] = sorted({f for d in bad for f in d})
            else:
                res["verdict"] = "multi_entry" if len(obs) > 1 else "ok"
            undeclared = [f for f in ("dp", "db", "mf", "xf") if f not in mode]
            if undeclared:
                res["undeclared"] = undeclared
        results.append(res)

    order = {"MISMATCH": 0, "multi_entry": 1, "ok": 2, "not_hit": 3, "no_contract": 4}
    results.sort(key=lambda r: (order[r["verdict"]], r["id"]))
    counts = defaultdict(int)
    for r in results:
        counts[r["verdict"]] += 1

    def fmt_c(c):
        if not c:
            return ""
        return " ".join(f"{k}={v:X}" if k in ("dp", "db") else f"{k}={v}" for k, v in c.items())

    lines = [
        "<!-- GENERATED by registry/check_entry_state.py - do not edit by hand. -->",
        "# Dispatch entry state vs CONTRACT",
        "",
        f"Observed with `ff4-port/desktop/ff4-entry-probe` over {len(fixtures)} fixtures × "
        f"{args.frames} frames, dispatch enabled (the state each native body actually receives). "
        "`MISMATCH` = a CONTRACT `entry_mode` field the game contradicts: the routine's spike "
        "replays a state the game never enters — re-spike under the observed state before "
        "trusting its level. `not_hit` = no fixture exercises it (no evidence).",
        "",
        "| Verdict | Count |", "|---|---|",
        *[f"| {k} | {counts[k]} |" for k in order if counts[k]],
        "",
        "| ID | Routine | Level | Verdict | CONTRACT entry_mode | Observed (dp db m x : hits) |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        if r["verdict"] in ("not_hit", "no_contract"):
            continue
        obs = "<br>".join(f"{o['dp']:04X} {o['db']:02X} {o['m']} {o['x']} : {o['hits']}"
                          for o in sorted(r["observed"], key=lambda o: -o["hits"])[:4])
        v = r["verdict"] + (f" ({','.join(r['mismatch_fields'])})" if r.get("mismatch_fields") else "")
        lines.append(f"| {r['id']} | `{r['name']}` | {r['level']} | {v} | {fmt_c(r['contract'])} | {obs} |")
    nh = [r["id"] for r in results if r["verdict"] == "not_hit"]
    lines += ["", f"Not hit by any fixture ({len(nh)}): " + ", ".join(nh)]
    args.out.write_text("\n".join(lines) + "\n")
    (HERE / "entry_state.json").write_text(json.dumps(results, indent=1) + "\n")
    print(" ".join(f"{k}={counts[k]}" for k in order if counts[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
