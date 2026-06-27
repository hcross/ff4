# RESTART — Selective asset reset

> The project is in an **unstable** state: successive fixes have piled up
> without always knowing which fix compensates for what. This restart aims to
> start over on a **structured** basis without discarding the lessons learned.

**Principle**: not a total restart from scratch, but a **selective reset by
layer**. We keep what's proven, revert the unproven back to the interpreter, and
requalify in order via [WF-DECOMP](workflows/WF-DECOMP.md) +
[WF-VALID](workflows/WF-VALID.md).

---

## Strategy

1. **Keep** the L3/L4 dispatches (oracle- or device-validated).
2. **Revert to pure interpreter** any unproven L0/L1 dispatch that introduces
   a drift risk — even at the cost of temporarily losing the perf gain.
3. **Requalify** each L1 → L2 → L3 routine in priority order, one at
   a time, logging the result in [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md).
4. **Document** every keep/remove/requalify decision, so the "why" is never
   lost again.

> ⚠ Honest starting state: **the registry is marked L1 by default** (except 1
> L0 stub) — caution, not truth. The runtime-equivalence infra already exists
> (`parity/` spikes + oracle), and the spike history (June) shows that
> many routines already have a per-routine runtime equivalence. The audit
> consists of **crediting** these validations (→ L2) and driving the missing
> ones to L2/L3, not redoing everything from scratch. (No bit-exact
> recompilation: abandoned path — see [AGENTS.md](AGENTS.md) §B.2.)

---

## Classification audit (DONE — 2026-06-27)

See [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md). Distribution:
**L0=1 · L1=56 · L2=141 · L3=5 · EXCL=3**. 134 routines promoted L1→L2 by the spike
batch (fuzzed runtime equivalence). 2 isolated FAILs (`CheckMenu_c`, `TfrBGAnimGfx_c`).

## Stabilisation decision (step 3 — 2026-06-27)

> **Conclusion: no reversion.** The audit invalidated the RESTART's initial
> premise ("revert the unproven L0/L1s to regain a sound base"). With
> 146 proven routines (L2+L3) and only 2 isolated real divergences, the
> base is **already stable**. Above all, **reverting is neither free nor always safe**:

- **DMA**: reverting a DMA routine to the interpreter path **hardfaults
  post-savestate on device** (F3). `TfrBGAnimGfx_c` (1 of the 2 FAILs) is a
  DMA routine (`output_ram` = `$43xx`/`$420B`/`$211x`) → **do NOT revert**.
- **WaitVblank / NMI**: some routines are dispatched *because* the interpreter
  path loops or is too slow (see F10). Reverting them reintroduces the hang.
- **Input (F5)**: `UpdateCtrlField_ext` & co. are intentional reimplementations
  incompatible with the interpreter harness.

Decision by category:

| Category | Count | Decision | Why |
|-----------|----|----------|-----|
| L2 (spike) + L3 (oracle) | 146 | **keep** | proven equivalence |
| EXCL (DMA-bypass) | 3 | **keep** | intentional divergence, device-safe |
| L0 stub (`ExecSound_ext_stub`) | 1 | **keep** | deliberate stub (unblocks the title) |
| FAIL `CheckMenu_c` (D0081F4) | 1 | **keep + investigate** | 1/400, rare-entry flow — likely artefact (WF-VALID) |
| FAIL `TfrBGAnimGfx_c` (D00CB5F) | 1 | **keep + investigate** | DMA → dangerous to revert; 2/400 |
| L1 build_error | 35 | **keep** | not-spikable ≠ broken; make the spike self-contained |
| L1 no_source (btlgfx) | 11 | **keep** | bundled bodies; custom spike required |
| L1 no_contract | 8 | **keep** | add a CONTRACT block, then spike |

The effort **shifts**: from "revert" to "closing the 56 L1s" (fixing the
build_errors, spiking the btlgfx, investigating the 2 FAILs). That's the real next step.

## Priority order — combat critical path

The restart follows the highest-impact game flow (combat), from root to
leaves:

1. **ATB timers** — `D039741` GetPendingAction, `D039788` CheckTimer,
   `D0397B3` InitAction, `D039E65/E71/F1C/F75` TimerDur, `D039FD8` ApplySpeedMod
   *(F11/F12 arc — to confirm at L3 via isolated WF-VALID)*
2. **Actions & commands** — `Cmd_*`, `do_*_emu` (currently no-op → damage
   swallowed, missing animations)
3. **Monster AI** — `RandAITarget_emu`, `SkipAITurn_emu`, `AITarget_*`, `AICond_*`
   *(observed bug: passive monsters under dispatch)*
4. **Magic effects** — `MagicEffect_*`, `MagicDmgEffect`
5. **Combat graphics** — `D038085` ExecBtlGfx, btlgfx monsters, `D03FE03`
   TfrSprites
6. **Return to field** — `field` routines on the combat-exit path

## Requalification tracking

| Batch (date) | Action | Detail |
|------------|--------|--------|
| Spike batch 2026-06-27 | requalify | 134 × L1→L2 (fuzzed runtime equivalence) |
| Step 3 2026-06-27 | keep | 0 reversion (stable base; DMA/WaitVblank revert dangerous) |

**Possible actions**: `keep` (already proven / risky to revert) · `requalify`
(L1→L2/L3 via workflows) · `remove` (revert to interpreter — **only if
safe**: not DMA, not WaitVblank, not input) · `port` (stub → real C).

---

## Link with the ongoing investigation

The combat bug documented in MemPalace (`[TASK] ff4-combat-visual-bugs`:
missing attack animations + passive monsters natively) is a **symptom**
of the unstable state. Fixing it goes through requalifying layers 2 and 3
above (actions/commands and monster AI), not through one more one-off patch.
