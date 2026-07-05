# WF-VALID — In-game behavioural validation

> Prove that a dispatch produces the **same behaviour** as the interpreter
> in a real gameplay situation, by isolating it in the oracle. Pushes a
> dispatch from **L2 → L3**.

**Tools**: `ff4-port/desktop/` (`ff4-desktop-oracle`, `wram_diff`,
`ff4-desktop-headless`, `proof_cyc`), `gnw-hardware:debug` (GDB for fine tracing).

---

## Input

- An already-ported dispatch (ideally L2) — ID `D<bank><addr>`.
- A hypothesis on where in the game the routine is exercised.

## Output

- A row in [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 2:
  savestate, frames, native/interp WRAM CRC, drift, final PC, maturity.
- Promotion to **L3** if drift is zero (outside the stack mask) and there is
  no execution divergence.

---

## Steps

### 0. Context recovery
Post-compaction protocol (AGENTS §B.4). `[TASK:ongoing] wf-valid-D<id>`.

### 1. Identify the usage point
Determine a scene where the routine is called. Cross-reference with
`KNOWN_FINDINGS.md` and `miss_profiler` (hot PCs). List the reference
savestates (`ff4-port/fixtures/*.lss`, private submodule); otherwise capture one via
`ff4-desktop-sdl` (`5` = incremental save slot).

### 2. Load a savestate leading to the usage moment
The savestate must reach a moment where **only this dispatch** matters. Verify
the routine is actually reached:
```sh
./ff4-desktop-headless $ROM --load ../fixtures/<scene>.lss --frames N --trace-frame F
# or watch an address written by the routine:
./ff4-desktop-headless $ROM --load ../fixtures/<scene>.lss --frames N --watch-wram <ADDR>
```

### 3. Isolate the dispatch in the oracle
Enable **only** the target routine, exclude everything else via the oracle's
exclusion filter (`--exclude HEX`, repeatable), or conversely start from
`oracle-baseline` and reintroduce only the routine under test.
```sh
cd ff4-port/desktop
make oracle SEED=../fixtures/<scene>.lss FRAMES=600        # A/B dispatch vs interpreter
```

### 4. Compare WRAM (CRC + byte-exact diff)
```sh
./wram_diff $ROM ../fixtures/<scene>.lss        # byte-exact diff, masks the stack region
```
- **0 diverging bytes** (outside the mask) → faithful.
- Divergence with a **cycle delta ~0** but PC 1 instruction off →
  **phase-skew artefact** (AGENTS §A.2), not significant: verify via
  `wram_diff` (byte-exact), not the per-frame CRC.
- Real divergence → step 5.

> ⚠ **Compare at equal SNES `frames_run`**, not equal headless frames:
> the interpreter is ~6× slower (AGENTS §A.2). Align both passes on
> the same `frames_run` (read from the `=== result ===` output).

### 5. Visual validation (mandatory for rendering)
For any routine touching display: dump the frame + **pixel-diff** against a
known reference.
```sh
./ff4-desktop-headless $ROM --load ../fixtures/<scene>.lss --frames N --out /tmp/cap.ppm
# convert + compare (sips → png, visual diff)
```
Corrupted rendering **is not** detected by fps/frame-count/fault alone
(`snes-re` rule §6). Never conclude "OK" from the mere absence of a crash.

### 6. Fine tracing on divergence (instrumentation)
- `--trace-frame F` to list the PCs dispatched on the diverging frame.
- Embedded `printf` in the C routine (the WRAM write-hook is blind to C).
- `proof_cyc` for frame-by-frame PC/cycle progression.
- On device: `gnw-hardware:debug` (GDB, oracle liveness, SCB/CFSR).
- Read the **first diverging addresses** from `wram_diff` → points at the bug.

### 7. Log in the registry (Table 2)
`ID | savestate | frames | native CRC | interp CRC | drift | final PC | maturity | date`.
Promote to **L3** if drift is zero and execution is aligned. Otherwise, stay at
the current level and open a MemPalace obstacle + (if relevant) a finding in
`KNOWN_FINDINGS.md`.

### 8. Closure
Update the `[TASK:*]`, ADR/obstacles, diary.

---

## Guardrails

- **Isolate**: only one active dispatch, otherwise drift isn't attributable.
- **Equal SNES `frames_run`** for any comparison (not headless frames).
- **Pixel-diff screenshot** for any rendering, never fps/frames/fault alone.
- **Byte-exact `wram_diff`** is authoritative, not the per-frame CRC (artefacts).
- The stack mask is legitimate; any other exclusion must be **commented**.
