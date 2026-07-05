---
name: ff4-custom-spike-author
description: "Author a standalone spike for one FF4 routine whose C body is
  bundled with others in a single .c file, so translator/generate_spike.py
  can't auto-generate a spike for it (the registry's next_task.py
  'custom_spike' bucket, e.g. routines inside ff4-gnw/battle/btlgfx_prim.c
  or btlgfx_monsters.c). Use once per routine — the bucket is small (11
  routines as of 2026-07-05, NOT the ~103 figure from an unrelated,
  never-merged experiment, see 'A note on the 103 figure' below). Produces
  an extracted single-function file, a working spike, and (if it passes) a
  registry promotion — never promotes on unverified evidence."
---

# ff4-custom-spike-author — spikes for bundled-body routines

## The problem, precisely

`translator/generate_spike.py` resolves one file to one routine: it reads
`module = source_path.parent.name` and `name = source_path.stem`, then
looks for a single `// CONTRACT:` block in that file. Several FF4
routines were ported into a **shared** file alongside others they're not
individually addressable from (`ff4-gnw/battle/btlgfx_prim.c`,
`ff4-gnw/battle/btlgfx_monsters.c`, and — a milder case — the two entry
points sharing one static body in `ff4-gnw/field/UpdateBG2Scroll.c`). The
tool can't pick one function out of a multi-function file, so it either
fails to parse a CONTRACT at all, or (for the `CONTRACT <Name>:` header
style these bundled files use) doesn't match `_CONTRACT_RE`'s stricter
`CONTRACT:` token at all. **This is not a limitation to design around —
it's an already-solved problem** (see below); the fix is per-routine
extraction, not a change to the generator.

## A note on the "103" figure

An old audit report cited "~103 custom_spike routines." That number is
real but **misattributed** — it's the count of `final_status: "custom_spike"`
entries in `ff4-port/translator/runs/cascade_log.jsonl`, an unrelated,
never-merged LLM-cascade benchmark over the `field` module. The actual,
current, registry-tracked bucket (`python3 registry/next_task.py`,
section `custom_spike`) is **11 routines**. Don't re-derive a bigger
backlog than exists — check `next_task.py`'s live count before assuming
scope.

## The proven pattern (don't reinvent — two worked examples exist)

`ff4-port/translator/port/battle/DrawMonsterSprite.c` (clean pass) and
`BuildOAMEntries.c` (passed after a real bug fix) are the reference
implementations. Read both in full before authoring a new one — match
their structure exactly:

1. **Extract the function body verbatim** into its own file,
   `ff4-port/translator/port/<module>/<Name>.c`, `#include`-ing only what
   it needs (`snes/snes.h`, `snes/cart.h` typically).
2. **Inline any same-file sub-call** the routine depends on (copy the
   sub-function's body into the new file too — see how
   `BuildOAMEntries.c` inlines `BackAttackYOffset_s_c`). Don't try to link
   against the bundled file; the whole point is a standalone compilation
   unit.
3. **Stub `inject_cycles` as a no-op** (`static inline void
   inject_cycles(Snes *snes, int n) { (void)snes; (void)n; }`) when the
   spike compares post-state, not cycle timing — true for essentially all
   of these (pure ROM→WRAM copies, OAM table builds, arithmetic
   primitives; nothing here drives HDMA mid-execution).
4. **Write one `// CONTRACT:` block** in the standard format (see any
   already-passing routine for the exact grammar):
   ```
   // CONTRACT:
   //   inputs_reg:  <regs the routine reads, e.g. x=8>
   //   inputs_ram:  <addr>=<width>, ...
   //   output_ram:  <addr>=<width>   (or use SPIKE_COMPARE: region — see below)
   //   entry_mode:  mf=<bool>, xf=<bool>, dp=<hex>, db=<hex>
   //   entry_flags: z=auto, n=auto
   ```
   Get `entry_mode` from the routine's **actual** calling context, not a
   guess — check `ff4-gnw/CONVENTIONS.md` for the module's verified DP/DB
   facts, or read how the bundled file's own (already-working) neighbor
   CONTRACT comments declare it; battle-module routines here are
   consistently `mf=true, xf=false, dp=0x0, db=0x7E` in the observed cases.
5. **Add `// SPIKE_COMPARE: region` and `// SPIKE_MASK: lo-hi[, ...]`**
   when the routine writes to a computed/indexed address (an
   `sta $XXXX,x`/`,y` in the source asm) rather than a fixed one —
   `generate_spike.py`'s indexed-store safety net (regex
   `_INDEXED_STORE_RE`) forces `CUSTOM_SPIKE` classification on these
   unless a region compare is declared instead of a fixed `output_ram`.
   Mask out any dead/irrelevant scratch bytes the original asm touches
   but your C port doesn't reproduce (found by running the spike once and
   seeing what differs outside the bytes that actually matter — this is
   normal, not a bug, for compiler-relevant scratch DP cells).
6. **Add a `REVERSED_FUNCTION:` fallback line** when the port's C name
   differs from the asm label `ca65-bridge` would resolve by name — e.g.
   `DrawMonsterSprite_c` is the asm routine `UpdateCharPalette`. Without
   it, `generate_spike.py` can't find the address at all. Format:
   `// REVERSED_FUNCTION: <module>::<AsmLabel> ($<bank>:<offset>)`.

## The single most important bug class to check for: register-width truncation

**This already happened once — BuildOAMEntries_c shipped with it.** When
the original asm computes an index via 8-bit accumulator arithmetic
(`TXA` with `mf=true`, then `ASL`/`ASL` — each 8-bit, each truncating —
then `TAY`), the natural-looking C translation
`(uint16_t)((uint16_t)x << 2)` is **wrong**: it doesn't truncate at 8 bits
the way real 8-bit `ASL` does, so it silently diverges once the shifted
value would exceed 255 (here: `slot >= 64`). The fix is to truncate at
the same width the asm actually computed in, then widen only after:
`(uint16_t)(uint8_t)(slot << 2)`, not `(uint16_t)((uint16_t)slot << 2)`.
**Before writing any shift/multiply on an 8-bit-mode-derived index, check
what width the asm actually computed in (`AGENTS.md`'s `m`/`x` flag
tracking, `docs/primer/02-65816-assembly-101.md` in the umbrella repo) —
don't default to "whatever C type is convenient."** Fuzzing with a full
`0-255` random input (see `generate_spike.py`'s default `host_rng()`
usage) reliably catches this class of bug if you write it, but it's much
cheaper to just get the width right the first time.

## Known blocker: register-output-only routines (do not re-attempt naively)

`generate_spike.py` can **only** compare WRAM (`output_ram:` or
`SPIKE_COMPARE: region`) — it has no `output_reg` comparison path. A
routine whose only observable effect is the accumulator/flags (no WRAM
write at all) generates a spike that silently compares two hardcoded
zeros (`out_asm = 0; out_c = 0; ok = (out_asm == out_c)` — always true).
**This produces a "fails: 0" that proves nothing.** Discovered 2026-07-05
on `D02BB0B`/`D02BB1A` (`BackAttackYOffset_s_c`/`_l_c`, $02:BB0B/BB1A) —
both correctly left at L1, NOT promoted, with the diagnostic saved as
`ff4-port/translator/runs/D02BB0B_backattackyoffset_s_BLOCKED_vacuous_spike.txt`
and `D02BB1A_backattackyoffset_l_revalidation.txt` (same finding, read
either in full before touching a register-output routine). **This is not
specific to those two** — `spike_getantielem_*.c` and `spike_max99_*.c`
already in `parity/src/` hit the identical hollow branch, meaning some
currently-recorded L2 routines' "passing spike" evidence may be equally
non-probative. That's a structural gap in the validation harness itself,
out of this skill's scope to fix (adding a real `output_reg` comparison
mode to `generate_spike.py` is a harness change, not a per-routine spike
— see the "What NOT to do" section) — flag it, cite the diagnostic files
above, and leave the routine at its current level. Do not promote a
register-output routine on a spike that declares no `output_ram` and no
`SPIKE_COMPARE: region` — verify by reading the generated spike's
comparison branch yourself if in doubt.

A register-output routine CAN sometimes be validated **transitively**: if
it's already inlined as a sub-call inside another routine's WRAM-output
spike (e.g. `BackAttackYOffset_s_c` is inlined into
`BuildOAMEntries.c`'s region-compare spike, which does exercise it with
real inputs and does check real WRAM output), that's real evidence — but
only if the inlined body is byte-identical to the one actually dispatched
at the routine's own address, and the claim should say explicitly
"validated transitively via <caller>'s spike," not imply a spike exists
for the routine standalone.

## Procedure

1. Pick one routine from `next_task.py`'s `custom_spike` bucket. Read its
   bundled source in `ff4-gnw/<module>/*.c` in full, and read the asm at
   its dispatch address in `ff4-port/upstream/notes/ff4j-sfc.asm` (via
   `ca65-bridge get-asm` if useful) to ground every line against the
   original, not just the existing C.
2. Extract per the pattern above into
   `ff4-port/translator/port/<module>/<Name>.c`.
3. Generate and build the spike:
   ```sh
   cd ff4-port
   python3 translator/generate_spike.py translator/port/<module>/<Name>.c
   cd parity && make ff4-spike-auto-<name-lowercase>
   ```
4. Run it with a real trial count (300 minimum, matching this project's
   existing convention), save the **full output to a file** under
   `ff4-port/translator/runs/` (don't just eyeball the terminal — the
   evidence file is what `registry_promote.py` requires):
   ```sh
   ./ff4-spike-auto-<name-lowercase> ../upstream/rom/ff4-jp1.sfc 300 \
       > ../translator/runs/D<ID>_<name-lowercase>_revalidation.txt 2>&1
   ```
   **Before actually promoting, re-run once more at a HIGHER trial count
   than the run that looked clean** (e.g. 300 → 1000+). A ~0.1-1%
   divergence rate (a rare input combination, not a deterministic
   threshold) can pass 300/300 by chance and only show up at a larger
   sample. This project has two confirmed instances of exactly this:
   `D00F535 UpdateBG2ScrollSkip_c` (0/300, then 2/500 — turned out to be
   a real dispatch-table bug, not a fluke) and `D02DCED BuildOAMEntries_c`
   (passed its original 300-trial promotion, then failed 4/1000 on a
   *different* line than the bug already fixed — a second, independent
   truncation bug in the same function, only surfaced by re-running with
   more trials after promotion). The larger confirmatory run is what
   actually earns the L2, not the first clean-looking one.
5. **If it fails**: read the diff, find the actual root cause in the asm
   (don't guess-and-check random C changes), fix, regenerate, rebuild,
   rerun. Repeat until `fails: 0` on a real, saved run — not a stale
   memory of an earlier attempt.
6. **If the routine you extracted is also the one actually dispatched**
   (i.e. `ff4-gnw/<module>/<real-file>.c` still contains the bundled,
   un-fixed body), apply the same fix there too and confirm the full
   desktop build still compiles clean:
   ```sh
   cd ff4-port/desktop && make headless-all
   ```
7. Promote, citing the evidence file you just wrote:
   ```sh
   python3 registry/registry_promote.py D<ID> --to L2 \
       --evidence ff4-port/translator/runs/D<ID>_<name-lowercase>_revalidation.txt \
       --note "<what was extracted/fixed, trial count, pass rate>"
   ```
8. Run `python3 registry/render_registry.py --check` and
   `python3 registry/migrate_registry.py --check` to confirm the registry
   and `DISPATCH_REGISTRY.md` stayed in sync.

## What NOT to do

- Don't modify `generate_spike.py`'s CONTRACT-parsing or classification
  logic to try to make it handle multi-function files automatically —
  that's a different, larger, unasked-for project. Per-routine extraction
  is the established, working pattern; use it.
- Don't promote a routine on a prior session's or a commit message's
  claimed pass rate. Re-run the spike yourself and save fresh evidence —
  `DrawMonsterSprite_c` sat at L1 for five days despite a real 300/300
  pass because nobody re-ran it and promoted at the time; verify, don't
  trust.
- Don't skip the width/truncation check above because "the C looks
  right" — it looked right the first time for `BuildOAMEntries_c` too.
- Don't touch a routine outside the `custom_spike` bucket — this skill is
  scoped to bundled-body routines specifically, not general spike
  authoring (that's `translator/generate_spike.py`'s normal, working
  path for standalone files).
