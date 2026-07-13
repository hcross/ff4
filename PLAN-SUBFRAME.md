# Sub-frame campaign plan — 60 fps under continuous scroll

> Next dedicated perf session. Starting point (2026-07-13, all measured on
> the `FF4_AUTO_WALK_LR` bench, 354 MHz, D6R homologous blocks):
> **26.2 ms/frame** continuous scroll (38.2 fps). Target: **< 16.7 ms**
> (60 fps) — **−9.5 ms to find**. The user's real free-roam walk is a mix
> of scroll and pauses: it sits well below the pure-scroll cost, so every
> ms recovered here lands directly on the worst-case feel.

## Ground rules (unchanged, now with the hardened flash protocol)

- One step = one measurement. D6R homologous blocks on the LR bench;
  byte-identical FB CRCs (7 fixtures incl. 010 vertical scroll + 900-frame
  walk) before any device cycle; revert anything ≤ 0 net.
- Flash protocol (mandatory since the OC-marginal-write incident):
  reset-halt before flashing → intflash + frogfs together → md5-verify
  both regions (`gnwmanager dump`) → check bank1 vectors after any erase.
- The desktop sampler over-estimates compose and misses device-only
  effects (R10b, R12, runLine-ITCM): it ranks *candidates*, the ring
  decides.

## Status after the 2026-07-13 evening pass

Step 0, lever 1's probe and a fused-compose attempt were executed the
same day; the plan below is updated with their verdicts:

- **Step 0 done.** Post-R15/R16 split: runLine 50.8% (~13.3 ms), compose
  22.3% (~5.8), memset 6.9%, APU ~12%, interpreter ~5%. Fine-grained PC
  histogram pinned ONE 128-byte loop at ~4 ms: the per-pixel
  raw->s_lrVal copy of the direct BG decode (~10 instr/px, 114k px/frame).
  R2b thrash ruled out by measurement (TRCMISS: 541 misses/frame walking
  = ~0.2 ms).
- **Lever 1 probe done: BG2 == BG1 within noise** (+/-25 ms/block).
  A second cache would land ~-0.6 ms/frame but needs 131 KB the margin
  cannot fund without sacrificing the R5 idle store. PARKED.
- **Fused compose->RGB565 (R17) tried and REVERTED: -0.083 ms/frame.**
  Third data point (after top-down compose and runLine-ITCM) proving the
  wall: ~6 equivalent 256-entry per-pixel traversals per line; removing
  one while adding a claim test to the others is a wash. The remaining
  render win must reduce per-pixel work in ALL passes at once -->
  **span-compose** (see below), not another pass fusion.
- Net kept from the pass: FF4_ML_LAYER probe knob + TRCMISS diagnostics
  (ff4-gnw `1f59d69`, ff4-port `39aa068`).

## Revised lever order

1. **Span-compose (the real render lever, structural).** At decode time,
   emit per-8px-tile span metadata (fully-opaque / fully-transparent /
   mixed + uniform priority). The compose then walks SPANS, claiming
   whole runs with memcpy-like inner loops and only falling back to
   per-pixel work on mixed spans. This cuts work in every pass at once
   -- the only shape the three neutral experiments say can win big.
   Estimated -2 to -4 ms, real refactor, needs the full CRC battery.
2. **APU tier 2** (unchanged, ~3.1 ms bucket): SPC opcode batching, then
   dsp flat rewrite. Estimated -1 to -2 ms combined.
3. **Sprite/OAM path** (within runLine's remainder) -- profile first.
4. **Adaptive pacing** as the user-gated fallback (unchanged).

## Step 0 — re-profile (30 min, do this first)

The 47/16/11.5/11 split predates R15/R16. Re-run the LR-sample
(~130 gdb halts on the LR bench) and re-rank. Expected post-R15/R16
shape, to be confirmed: runLine (BG2 direct decode + BG1 extraction +
sprites + glue + output) ~12 ms, compose ~4.3, APU ~3.3, interpreter
~2.4, blit 0.34.

## Lever 1 — BG2 map-space cache (decision gate: RAM)

R16 covers BG1 only; BG2 (4bpp, wider+higher) still walks the direct
span decode every line. Two sub-steps:

1. **Cheap value probe (1 build):** swap the R16 cache to layer 1
   instead of layer 0. If BG2 gains ≈ BG1's −0.63 ms, the two-layer
   total is ~−1.3 ms and justifies the RAM surgery; if it gains much
   less (sparser layer), stop here.
2. **RAM surgery options for the second 131 KB** (current margin 17 KB):
   - `s_psSub` (57 KB) is only read on math+subscreen replay paths —
     field has none. Making the R5 store math-less (drop s_psSub, keep
     psPix+psFlg) frees 57 KB; measure the idle path stays intact.
   - R2b tile-row cache: BG1 no longer hits it under scroll (R16
     bypasses it in steady state); 2048 → 1024 slots frees 24 KB.
     Watch the title/menu scenes that still use it.
   - Remaining ~33 KB: shrink ML_W to 512 shared slots with (layer, ly)
     tags is NOT viable (448 live lines > 256 slots, thrash) — prefer
     512-px lines for BG2 in a dedicated 131 KB block, or accept
     BG1-only if the probe says BG2 is cheap anyway.

## Lever 2 — compose reads map-space (kills the extraction copy)

R16 still copies 256 px (val u16 + prio u8 + hasPrio tests) per line per
cached layer into `s_lrVal`/`s_lrPrio`. Teach the BG branches of
`ppu_lrComposeLine` to read `ml[(x + hScroll) & 511]` directly for
cached layers (val = b & 0x7f, prio = b >> 7):

- hasPrio per window: over-approximate per map line at decode time
  (any-p0/any-p1 across the 512 px) — a superset only ever *adds* a
  compose pass, never skips a needed one; correctness invariant.
- The 4 compose loops gain a variant (cached vs direct source); gate it
  to layers with a valid ml slot for this line — pass the slot index
  down from the decode stage.
- Estimated −0.5 to −1.5 ms (the extraction cost measured inside R16's
  −0.63 residual). Medium risk: touches every compose path — the FB CRC
  battery is the safety net.

## Lever 3 — APU tier 2 (~3.3 ms bucket)

Byte-exactness bars state-observable shortcuts (ENDx/decodeOffset are
driver-visible). Two structural options, in order:

1. **SPC opcode batching**: `spc_runOpcode` pays fetch/decode dispatch
   per opcode (~9.4 KB switch, now in ITCM). Batch N opcodes between
   timer syncs (apu_syncTimers already materializes counters on access,
   A1 groundwork). Estimated −0.5 to −1 ms, medium risk.
2. **dsp_cycle flat rewrite**: restructure per-sample work into a
   channel-major loop with early-outs; keep every observable store
   (OUTX/ENVX/ENDx/echo RAM) bit-exact — AUDCRC is the evidence channel.
   Estimated −0.5 to −1.5 ms, higher risk, bigger diff.

## Lever 4 — sprite/OAM path (size TBD by step 0)

`ppu_runLine` still evaluates sprites per line (R9 line map) and the
corridor has ~6 NPC sprites. If step 0 shows a meaningful sprite bucket:
memoize per-line sprite evaluation keyed on (OAM gen, line) — OAM
changes once per frame (DrawNpcs), lines re-evaluate 224× against the
same OAM. Estimated −0.5 to −1 ms.

## Fallback — adaptive frame pacing (UX decision, last resort)

If the levers land ~21-22 ms scroll (46+ fps) and 16.7 stays out of
reach: an *adaptive* skip (render-skip only when the emulated frame
overruns, odd-period guard against the 30 Hz alias) trades a rare
skipped render for full-speed game logic. Distinct from the fixed
FF4_FRAMESKIP the user rejected ("slideshow") — needs his sign-off
with a live A/B on device.

## Session checklist

1. `ff4-status` bootstrap + MemPalace sweep (checkpoint the handoff drawer).
2. Step 0 re-profile → re-rank this plan.
3. Levers in measured order; one commit per kept step, revert the rest.
4. Close: playable build (no AUTO_WALK) + user verdict on his real walk,
   BACKLOG entry, MemPalace checkpoint, push everything (retro-go-sd
   pushes stay at the user's hand).
