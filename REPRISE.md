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

## Classification audit (to be done)

For each of the 206 dispatches, determine the **real** state:

- [ ] Classify as L0 / L1 / L2 / L3 / L4 per the AGENTS §B.2 criteria
- [ ] Identify **residual no-op stubs** in the table (empty body or a
      no-op `_emu` call) — candidates for immediate removal
- [ ] Spot **compensating fixes** (a fix that masks another
      bug) — to be decorrelated
- [ ] Flag dispatches with **intentional DMA-bypass** (excluded from baseline:
      `D15CADC`, `D048004`, `D03FE03`, `D15CA5E`) — special status, not strictly
      L3

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

| Routine (ID) | Level before | Action | Level after | Date | Ref |
|--------------|--------------|--------|--------------|------|-----|
| _(to be populated as the restart proceeds)_ | | | | | |

**Possible actions**: `keep` (already proven) · `requalify` (L1→L2/L3 via
workflows) · `remove` (revert to interpreter) · `port` (stub → real C).

---

## Link with the ongoing investigation

The combat bug documented in MemPalace (`[TASK] ff4-combat-visual-bugs`:
missing attack animations + passive monsters natively) is a **symptom**
of the unstable state. Fixing it goes through requalifying layers 2 and 3
above (actions/commands and monster AI), not through one more one-off patch.
