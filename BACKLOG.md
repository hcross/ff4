# BACKLOG — Realigning existing → target

> Workstreams to bring both projects in line with the organization described in
> [AGENTS.md](AGENTS.md). Checkboxes, with owner (🤖 agent / 🧑 human)
> and dependencies. Distinct from [REPRISE.md](REPRISE.md) (routine
> requalification) — here, the **infrastructure** of the effort.

---

## 1. Umbrella directory & submodules

- [x] 🤖 Create `ff4/` with `CLAUDE.md` (`@AGENTS.md`) and `AGENTS.md`
- [x] 🤖 Write the tracking documents (`DISPATCH_REGISTRY`, `BACKLOG`, `REPRISE`)
- [x] 🤖 Write the workflows (`WF-DECOMP`, `WF-VALID`, `WF-RELEASE`)
- [x] 🤖 Push the local `ff4-gnw` commits (→ `origin/main` bf685b5)
- [x] 🤖 Push the local `ff4-port` commits (→ `origin/main` da2e5dc)
- [x] 🤖 Initialize `ff4/` as a git repo + create `hcross/ff4` (public) on GitHub
- [x] 🤖 Move the working trees under `ff4/` and mount them as submodules
- [x] 🤖 Relative paths preserved (`FF4GNW ?= ../../ff4-gnw` → `ff4/ff4-gnw` ✓,
      savestates `../*.lss` moved along with `ff4-port` ✓)

## 2. Dispatch registry

- [x] 🤖 Populate Table 1 from `dispatch_all.c` (206 entries, initial level L1/L0)
- [x] 🤖 Audit each dispatch (2026-06-27) — evidence-based levels:
      L0=1 · L1=190 · L2=7 · L3=5 · EXCL=3. Sources: hardcore_log PASS,
      KNOWN_FINDINGS (wram_diff=0), fixes F10/F12, DMA-bypass excluded.
- [x] 🤖 Bulk L1→L2 promotion (2026-06-27): `translator/batch_spike_ffgnw.py`
      on the `ff4-gnw` bodies — **134 PASS** credited L2 (fuzzed spike, 200 trials).
- [x] 🤖 Break down + resolve the 35 “build_error” (2026-06-28): 12 delegate
      → DELEG; 19 run_hang (false hangs = compound budget, rerun with reduced trials
      / long run-timeout → **L2**); 2 parser_error UpdateBG2Scroll (hardened parser
      → **L2**); 2 compile_error remain.
- [ ] 🤖 Handle the 2 `fail` (real divergences): `CheckMenu_c` (1/200),
      `TfrBGAnimGfx_c` (2/200, DMA) — via WF-VALID
- [ ] 🤖 2 `compile_error`: `RandXA_c` (depends on `Div16_c` not included + 3-arg
      call); `TfrVRAM_c` (`#include dispatch_all.h` missing from the spike build)
- [ ] 🤖 Add a CONTRACT to the 8 `no_contract`; custom spikes for the 11
      `no_source` (btlgfx bundled in `battle/btlgfx_prim.c`/`btlgfx_monsters.c`)
- [ ] 🤖 Fill in Table 2 (oracle validation) as WF-VALID progresses
- [ ] 🤖 Fill in Table 3 (releases) as WF-RELEASE progresses

## 3. Runtime equivalence & tests *(infra largely EXISTING)*

- [x] 🤖 ~~Bit-exact c65 ASM recompilation~~ — **abandoned** (cc65 targets the 6502,
      unreachable; proof = runtime equivalence, cf. ADR oracle/WF-DECOMP)
- [x] 🤖 **Per-routine runtime** equivalence harness: `parity/` +
      `translator/generate_spike.py` (C spike vs interpreted asm) — EXISTS
- [x] 🤖 **ROM/frame** equivalence: `ff4-parity-compare` + `oracle_ab` — EXISTS
- [ ] 🤖 **WF-DECOMP §5** — extend the spike harness to inject **synthetic
      input states** (edge cases: 0, max, carry, overflows, extreme
      indices) that savestates never traverse
- [ ] 🤖 Wire `generate_spike.py` onto the current `port/` tree and re-validate
      in bulk (credit the L2s in the registry — cf. §5 Reprise)
- [ ] 🤖 Automate the release oracle (GDB batch) to minimize the human (WF-RELEASE §5)

## 4. MemPalace documentation

- [x] 🤖 ADR for the 5 reorganization decisions (`wing=ff4-gnw, room=architecture-decisions`)
- [ ] 🤖 Verify that `wing=snesdev` is populated (`snes-re` reference)
- [ ] 🤖 Migrate the durable findings from `KNOWN_FINDINGS.md` to MemPalace if relevant

## 5. Routine requalification

See [REPRISE.md](REPRISE.md) — dedicated workstream, tracked separately.

- [x] 🤖 L0→L4 classification audit of the 206 dispatches (actual state) — see
      [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md) Table 1
- [ ] 🤖 Ordered requalification list (combat critical-path priority)

## 6. Known technical debt (from KNOWN_FINDINGS + dispatch_all.c)

- [ ] 🤖 `do_*_emu` no-op (`do_fight_cmd_emu`, `do_magic_attack_emu`,
      `do_multi_attack_emu`) → real port to re-enable `Cmd_0f/0e/0c/08/01`
- [ ] 🤖 `RandAITarget_emu`, `SkipAITurn_emu` no-op → passive monster AI in dispatch
      (observed bug: monsters do not counter-attack, cf. `[TASK] ff4-combat-visual-bugs`)
- [ ] 🤖 `TimerDur_0b/03` — ROM bank $0F access (`snes_readByte` instead of `ram[]`)
- [ ] 🤖 `TimerDur_07` — dispatch wrapper for the non-standard signature `(Snes*, uint16_t x)`
- [ ] 🤖 `ExecSound_ext_stub` — real SPC responder (re-enables music/SFX)
- [x] 🤖 `gen_dispatch.py` — resolved in the opposite direction (2026-07-03):
      the rich per-entry comments and hand-tuned oracle machinery in
      `dispatch_all.c` make full regeneration infeasible without an engine
      to preserve them, and a real regeneration attempt was confirmed
      destructive (186 lines of oracle machinery lost, 206→201 entries).
      `gen_dispatch.py` is now read-only: it reports candidate routines not
      yet in the table (`python gen_dispatch.py`) without ever writing
      `dispatch_all.{h,c}`. Table edits stay manual, per
      [workflows/WF-DECOMP.md](workflows/WF-DECOMP.md).

### Device debt from the desktop bug-hunt (2026-06-29)

Bugs correct on desktop; still to be made **device-correct** (cf. MemPalace
`obstacles-and-solutions`):

- [x] 🤖 **Bug 3 mode-7** — `InitMapRAM` MMIO: REAL device FIX (1a86d23)
- [ ] 🤖 **Bug 4 tiles** — `TfrBGGfx`: faithful `snes_write` port (e02a9e4) but
      DMA-from-C does not flush (class F6) → interpreted on desktop. Device-correct
      port = **manual VRAM loop** (`TfrSprites_c`/F6 model); reads the
      pre-set DMA source (`$4302-4`), writes to `$2118/$2119`.
- [ ] 🤖 **Bugs 1+2 combat/menu** — requalify the **btlgfx batch** (14 no_source
      routines, eee0a51): **dynamic** bug (flicker/animation), several
      faulty routines chained (oracle bisection frame 0→1→3). Bisection by
      static dump impossible; go through the per-frame oracle or per-routine
      A/B SDL. Worked around on desktop via `host_exclude_divergent`.
- [x] 🤖 **MMIO re-audit (2026-06-29)** — systemic class: the LLM port
      hallucinated `sta $21xx/$42xx` as `ram[0x..]` (WRAM) instead of the bus. Scan
      `ram[0x21xx/0x42xx/0x43xx]` + sort by input DB.
- [x] 🤖 Fixed (DB=$00, non-DMA, snes_write, verified without regression):
      IncBrightness, AfterCutscene, LoadOverworldIntro, ExecBattle, InitWorld
      (+ earlier InitMapRAM). Commit ff4-gnw 1741b71.
- [x] 🤖 `TfrBGGfx` — **manual VRAM loop** (c2fc6f1): bug 4 tiles RESOLVED
      (real device+desktop fix, F6 model). No longer excluded.
- [x] 🤖 **DMA class handled** (2026-06-29, ff4-gnw 08405b1):
      `InitDMA` (setup regs), `TfrInvertPal`+`TfrBGAnimGfx`+`TfrBGGfx` (manual
      loop), `TfrLavaGfx` (bus+ROM table+delegate), `CloseYesNoWindow`
      (bus+ExecDMA delegate), `InitDMA_emu` wired up. `TfrPal` = delegate (not a bug).
      Regression-clean; TfrBGGfx/TfrBGAnimGfx visually validated.
- [ ] 🧑 **Visual validation of the 3 without repro**: `TfrInvertPal` (palette invert),
      `TfrLavaGfx` (lava anim), `CloseYesNoWindow` (Yes/No window close) —
      capture a scene exercising them to confirm the effect (faithful port + regression
      OK, but the specific effect not observed).
- [ ] 🤖 **Check the DB=$7E / DB=ROM cases**: `_13ddd6/_13eb60/_13ebb8/ExecInterrupt/
      InitCharRows/PlayGameSfx/PlaySystemSfx` (DB=$7E → `$7E:21xx` = WRAM, presumably
      OK) and `LoadTheEndGfx/_13e058` (DB to be confirmed). Confirm case by case.

## 7. PPU render-loop performance (title screen lag, 2026-07-06 investigation)

Triggered by a real on-device report: the title screen lags on G&W hardware.
Initial assumption was "needs more dispatch coverage" (CPU/65816 interpretation
is ~6x slower per §A.2) — **investigation disproved this** and redirected the
fix target. Full narrative in MemPalace `wing=ff4-gnw room=obstacles-and-solutions`
(drawer title: "PPU render-loop dominates title-screen cost, not CPU dispatch").

- [x] 🤖 Measured dispatch-hit rate boot→title (`miss_profiler`, 1800 frames):
      already ~86% by call count. 10/11 remaining miss PCs are one-shot boot
      inits (sound/controller/OAM, negligible cost); the 1 repeating miss
      (`$00:913E`, `WaitVblankShort` body, ~99.4% of miss volume) is a genuine
      NMI spin-wait — same unsafe-to-synchronously-dispatch category as
      `ExecBtlGfx`/`CheckMenu` (a C body can't wait for an NMI that hasn't
      happened). The project's own DELEG pattern for this class doesn't save
      any interpreted-opcode cost either — porting it wouldn't move the needle.
- [x] 🤖 Real wall-clock A/B (`ff4-desktop-headless --frames 600` vs
      `--no-dispatch`, equal `frames_run=599`, 3 runs each): dispatch ON is
      **~6% SLOWER** wall-clock than pure interpretation for this specific
      window (2.18s vs 2.05s) — dispatch call-count % is not a reliable proxy
      for real lag here.
- [x] 🤖 macOS `sample` (5s, `/usr/bin/sample`) on the running headless title
      loop: **`ppu_getPixel` 62%, `ppu_runLine` 15%, `snes_runCycles` 12%,
      `cpu_doOpcode` <0.1%**. The 65816 interpreter is statistical noise — all
      real cost is in LakeSnes's software PPU pixel renderer
      (`ff4-gnw/snes/ppu.c`), an architecture completely orthogonal to
      dispatch/CPU porting.
- [x] 🤖 Root-caused why THIS scene is expensive: `$2130`/`$2131` (CGWSEL/
      CGADSUB) enable SNES color math (BG1 main + BG2 sub, half-color blend —
      likely the logo/crystal glow effect), which makes `ppu_handlePixel` call
      `ppu_getPixel` **twice** per output pixel (main + subscreen) plus run the
      blend arithmetic. This is required for correct visual output, not waste.
- [x] 🤖 Checked for a free win in `ppu_getPixel`/`ppu_getPixelForBgLayer`: a
      per-scanline tilemap+bitplane cache **already exists** (`s_bgTilemapAdr`/
      `s_bgPlaneAdr`, comment: "cuts ~7/8 of BG-layer VRAM fetches") — the
      obvious memoization is already done. Remaining per-pixel cost (bit
      extraction from already-cached plane words) is inherently pixel-varying;
      no further win without changing what's rendered.
- [x] 🤖 **Batching lever implemented, measured, and PARKED (2026-07-06,
      branch `perf/ppu-bg-line-batching` in ff4-gnw — two commits, both
      byte-identical-proven against 19 golden runs: PPM + WRAM CRC over
      coldboot + 8 fixtures × 2 frame counts)**. Tip = variant A
      (whole-line lazy decode per BG layer); tip~1 = variant B (8px block
      decode, addSubscreen-gated). Fair alternated A/B on x86, medians:
      - Variant A: title −6%, combat −8%, **menu +23% / mode7 +13%
        regressions**, and pathological delegated-spin fixtures (003
        measured; 002/005/006 same class) **>15× faster** — would make
        them usable in desktop validation for the first time.
      - Variant B: title −5%, everything else +4..7% — trades away both
        the wins and the losses.
      Verdict: no variant is a clean win on x86; NOT merged to main.
      Regressions persist even where the fast path cannot engage
      (mode 7) — codegen/inlining sensitivity of the hot loop, not logic.
- [x] 🧑 **Device verdict (2026-07-08)**: branch flashed (merged tip
      `88e2a9c` = variant A + the pixelBuffer fix below) and observed:
      title ~3-5 fps → ~6-8 fps (~2×, human estimate), zero
      crash/visual bug through boot → title → intro → bridge dialogue.
      Attribution between batching and the pixelBuffer fix is ambiguous
      (flash `main` alone to separate them). Registry Table 3 has the
      release row. The M7 gain is real but the per-pixel renderer
      remains the structural floor.
- [x] 🤖 **Device link was silently BROKEN on main (found 2026-07-08,
      fixed same day)**: the 2026-07-06 battle/field fixes pushed the
      FF4 RAM_EMU overlay ~3 KB over budget (`Error: FF4 BSS overflow`)
      — never noticed because no device build had run since `225a397`
      (June 25). Fixed structurally on main (`004e78d`): the LakeSnes
      pixelBuffer stored an 8-byte hires PAIR per SNES column while FF4
      never uses hires and every reader only consumed the left half —
      halved to 256×4×224 under `FF4_PORT_STATIC_SNES` (−229 KB, 3
      fewer RAM writes/pixel, byte-identical over the 19-run golden
      sweep). Link margin: −3,024 B (fail) → +226,544 B. Lesson: any
      ff4-gnw commit adding code/BSS should at least device-LINK before
      merging (WF-RELEASE §3 build, no flash needed).
- [ ] 🤖 **Frameskip (not implemented — likely the biggest perceived-speed
      lever)**: the device loop (`main_ff4.c`) renders every SNES frame,
      so 6-8 fps displayed = game logic at ~1/8 speed. Rendering
      dominates (~85%+); emulating N frames while rendering only the
      Nth (keep `ppu_evaluateSprites` for game-visible $213E flags,
      skip only the pixel loop) would speed the game up almost
      proportionally. Needs a render-skip flag through
      `snes_runFrame`/`ppu_runLine` + a WRAM-identical validation pass.
- [ ] 🤖 **The structural fix — now sized by REAL M7 numbers (D6,
      2026-07-09, title screen, frameskip-3 decomposition)**: pure
      emulation 68 ms/frame + PPU render 186 ms/frame + blit 2 ms
      (3.3-3.9 fps). 60 fps (16.7 ms) therefore requires BOTH axes;
      a free renderer alone caps at 14.7 fps. Milestone plan:
      **M1** per-line layer renderer (render 186 -> target <20 ms;
      byte-identical golden bar, infra ready; also D-cache-friendly on
      the 16 KB M7 cache). **M2** vblank-spin fast-forward (emulation
      68 -> target ~15-20 ms on idle scenes: the title spins WaitVblank
      interpreted and snes_runCycles ticks ~357k events/frame -- the
      stepping machinery, not the opcodes, is the cost; detect the spin
      PC and advance cycles in bulk; WRAM-identical desktop validation).
      **M3** re-measure D6; if total >33 ms, next lever is
      snes_runCycles event batching (core surgery) and/or continued
      dispatch. Honest target: title 30-40 fps after M1+M2; strict 60
      likely needs M3. Order matters: M1 first (render dominates).
- [x] 🤖 **M3 (promoted after the M1 probe sampling showed snes_runCycle at
      ~67% of the M7 frame): snes_runCycles event batching — implemented and
      byte-identical-validated (2026-07-09, ff4-gnw branch
      `perf/runcycle-event-batching`, commit `fc3acb7`, on top of the M1
      line-renderer branch)**. The per-tick loop (~357k ticks/frame paying
      the full irq/event/wrap check chain) is replaced by segment runs
      between the only hPos values that owe event work (0/16/512/1104,
      h-irq point, line end); irq edge detection, event order and the apu
      catchup accumulation are preserved tick- and bit-exact (fp additions
      replayed, not fused). Validation: 41/41 byte-identical goldens
      (coldboot + 11 fixtures × 2 depths, PPM+WRAM) + 1800/1800 per-frame
      fb CRCs (006/012/013 × 600). Desktop wall-clock neutral (expected —
      same as M1, x86 OoO masks the stepping cost). **D6 measured on device
      (same day, title, FF4_FRAMESKIP=3): emu 67.8 → 59.0 ms (−13%), fps
      11.4 → 12.7 (+11%), render/blit unchanged** — same-day A/B reflash of
      the M1 tip in identical conditions, D6 windows stable to <0.1%.
      Correction to the historical record: the M1-era "render 63 ms" is not
      reproducible (the M1 tip itself reads 77.3 ms in today's conditions);
      render at ~77 ms is now unambiguously the dominant axis. Registry
      Table 3 has the release row. Remaining emu-side levers: the bit-exact
      fp-replay of the APU tick accumulation (removing it is NOT
      byte-identical → needs an ADR relaxing the bar for that accumulator),
      cpu-level batching of the WaitVblank spin (M2), continued dispatch.
- [ ] 🧑/🤖 **Not investigated**: whether the on-device (Cortex-M7) bottleneck
      profile actually matches the desktop x86 `sample` result — worth a
      cross-check before investing in the PPU refactor (different cache/memory
      characteristics could shift the hot path).
- [ ] 🧑 **Pragmatic alternative not tried**: throttle the title screen
      specifically to 30 fps (non-gameplay screen, likely imperceptible) —
      cheap to test, no shared-code risk, doesn't fix the underlying PPU cost
      but may be sufficient to eliminate perceived lag.

---

**Legend**: 🤖 doable by agent · 🧑 requires the human (hardware, push,
decision). `[x]` = done · `[ ]` = to do.
