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
      Table 3 has the release row. ADR-006 (ff4-port) authorizes an exact
      integer reformulation of the APU accumulator with a replacement
      evidence pack (not byte-identical by construction).
- [x] 🤖 **Probe sampling profile on the M3a firmware (240 samples, title,
      frameskip 3, 2026-07-09)** — the "measure before optimizing" pass
      for iteration 3. Full histogram + sampler pitfalls in MemPalace
      (obstacles drawer 60ef55ba). Headlines: `snes_runCycles` still #1 at
      26.7% but its fp-replay loop is only ~12% of that (~2-3 ms/frame —
      NOT the 7-9 ms estimated); the dominant cost is per-call overhead
      (~90k invocations/frame at 3-6 ticks per memory access).
      `ppu_getWindowState` is 8.3% of total wall — ~26 of the 77 ms
      render (34%): per-PIXEL window evaluation in the M1 compositor's
      output stage. Memory-access chain ~22.5%; real APU/DSP ~9%.
- [x] 🤖 **R1 — window state by spans in the M1 compositor — DONE,
      measured (2026-07-10, ff4-gnw branch `perf/r1-window-spans`,
      commit `7a974c7`, merged to main after Hoani's LCD confirmation)**: the s_lrWin
      per-line fill now sorts the 4 window-edge breakpoints and calls
      ppu_getWindowState once per span (≤5) + memset, keeping the
      original function as the single semantic authority. 41/41
      byte-identical goldens + 1800/1800 fb CRCs vs the M3a build.
      Device D6 (title, frameskip 3): render 77.2 → 47.0 ms (−39%,
      better than the ~24 ms estimate), emu unchanged 58.2 ms, title
      12.7 → 14.1 fps. Cumulative since the 2026-07-09 M1 reference:
      11.4 → 14.1 fps (+24%). **The walls have swapped: emulation
      (58 ms) is now the dominant axis again, render (47 ms) second** —
      E1 (ADR-006 accumulator + downcounter fast path) is the next
      lever, then E2/render-iteration-4 by whichever D6 says dominates.
- [x] 🤖 **E1 — exact integer APU debt + next-event downcounter fast path
      — DONE, measured (2026-07-10, ff4-gnw branch
      `perf/e1-apu-int-downcounter`, commit `a3f3337`, merged to main after
      input confirmation)**: int64 numerator against the rational
      clock ratio replaces the fp replay (ADR-006; .lss double view kept,
      states load unchanged); calls fitting inside the cached
      ticks-to-next-event budget are O(1). Hard-won invariant: positional
      events are owed by the tick STARTING at the boundary, the line wrap
      by the tick ENDING at lineEnd — the wrap tick never counts as
      fast-path budget (first cut hung combat fixtures via a 65536-cycle
      runaway line). Validation EXCEEDS the ADR-006 pack: 41/41
      byte-identical vs R1 (integer truncation coincides with the fp
      history over the whole coverage) + self-consistency + oracle
      verdicts unchanged 7/7. Device D6 (title, frameskip 3): emu
      58.2 → 43.6 ms (−25%), render untouched at 47.0, title
      14.1 → 17.9 fps. Cumulative since 2026-07-09 M1: 11.4 → 17.9
      (+57%). Walls now nearly balanced: render 47.0 / emu 43.6 →
      re-profile before choosing E2 vs render iteration 4.
      POSTSCRIPT — device-input incident, root-caused same day: E1 is the
      only change altering the Snes struct layout, and retro-go-sd's
      dependency include only globbed build/*.d (never build/<port>/*.d),
      so the incremental device build rebuilt snes.o alone and shipped a
      mixed-layout firmware — input dead on device, desktop (single-shot
      compile) unaffected, D6 numbers unaffected (main_ff4 statics).
      Fixed in the scaffold branch (retro-go-sd 0c9923a2: include
      build/*/*.d) + full build/ff4 rebuild; input and 17.9 fps both
      confirmed on the coherent binary. Lesson recorded in MemPalace
      obstacles: any external/ff4 HEADER change before that commit
      requires rm -rf build/ff4.
- [x] 🤖 **E2 — per-access memory chain, re-ranked #1 by the post-E1
      profile (240 samples, coherent E1 firmware, 2026-07-10)**: the
      whole per-access chain now costs **35.1%** of wall — snes_cpuRead
      12.5% + dma_handleDma 9.2% + cart_read 4.6% + snes_rread 3.8% +
      getAccessTime 3.3% + cpuIdle 1.7% (~19.6 ms/frame-avg). Design:
      flat region LUT (bank<<3|adr>>13 → {direct pointer, access
      cycles, kind}) for the WRAM/ROM fast cases + a single dmaPending
      byte guard so dma_handleDma's early-out becomes one load+branch.
      Timing-neutral → standard byte-identical bar. Remaining post-E1
      profile for the record: ppu_runLine 13.8% (sprite eval + render),
      snes_runCycles 13.3% (halved by E1 ✓), CPU interpreter core
      ~15.8% (dispatch's territory), APU/DSP ~12.9% (🧑 decimation =
      audio-quality decision), ppu_getWindowState gone from the top
      (R1 ✓). Projection if E2 recovers half its axis: title ~24-25 fps. MEASURED
      (2026-07-10, ff4-gnw `11f9fcb`, merged to main after player-level
      confirmation): emu 43.6 -> 31.3 ms (-28%), render untouched at
      47.0, title 17.9 -> 22.9 fps. Cumulative since the 2026-07-09 M1
      reference: 11.4 -> 22.9 fps (+101%, speed doubled across four
      byte-identical surgeries). Render (47 ms) is now the dominant wall
      again (1.5x the emu axis) -> next lever is render iteration 4
      (fresh probe profile of ppu_runLine internals first), then
      continued dispatch (CPU interpreter core ~16% pre-E2) and the APU
      decimation decision (~13%, human audio-quality call).
- [x] 🤖 **Iteration-4 probe profile + R2a (2026-07-10, ff4-gnw
      `ec00330`+`28e19b9`, merged to main)**. Frameskip-0 title profile
      (240 samples) decomposes the 47 ms render: ~17 ms BG decode
      (inlined ppu_lrDecodeBgLine), ~16 ms output stage, ~10 ms compose,
      ~3 ms sprite eval. R2a caches the final palette (cgram x
      brightness, keyed on a new ppu->cgramGen) and collapses the whole
      output stage to palette copies on lines with no math/clip/direct
      color. Measured (deterministic savestate-boot A/B on fixture 009,
      frameskip 0): field scene 76.5 -> 71.2 ms/frame (-7%), title
      neutral by design. LESSON: a per-pixel variant of the same
      shortcut cost +4.2 ms on the math-heavy title (duplicated tests;
      same codegen-sensitivity class as the parked 2026-07-06 batching
      variants) and was dropped after the device A/B caught it — the
      measure-every-increment discipline is what saved it.
- [x] 🤖 **R2b — decoded-tile-row cache — DONE, measured (2026-07-10,
      ff4-gnw `383052d`, merged to main)**. Hypothesis verified first:
      instrumented VRAM writes/frame = 0 on title, 0 on ~5/6 field
      frames, so a vramGen-invalidated cache hits ~100% on the target
      scenes. 4096 direct-mapped slots keyed on (planeAdr, bitDepth),
      raw 8-pixel column-order rows before hFlip/palette. Device D6
      (deterministic savestate-boot A/B, fixture 009, frameskip 0):
      field 71.2 -> 62.9 ms/frame (-12%), field fps 14.0 -> 15.8.
      Device framebuffer captured via probe = clean render. 41/41
      byte-identical goldens + oracle verdicts unchanged 7/7.
      Cumulative field render since E2: 76.5 -> 62.9 ms.
- [ ] 🤖 **Next render levers toward 60 fps** (field now ~63 ms; 60 fps
      = 17 ms, still ~3.7x): compose stage (~10 ms, s_lrPix/s_lrLayer
      memsets + per-layer loop -- cache or skip when the composed line is
      unchanged); dirty-line rendering (skip recompose of lines whose
      inputs -- scroll, VRAM, cgram, OAM -- did not move; the big
      structural win for static/scrolling scenes, but a real refactor);
      continued dispatch (CPU interpreter core); APU/DSP decimation
      (~13%, human audio-quality call). 60 strict likely needs the
      dirty-line refactor; 30-40 fps field reachable with the cheaper
      levers first.
- [x] 🤖 **R3 — loop-invariant branch hoists (compose + R2b apply),
      2026-07-10, ff4-gnw `cd0a678`, merged**: field render 62.9 -> 61.8
      ms (-1.7%). Confirms the cheap micro-opts are near their ceiling;
      compose is structurally branch/memory bound. Byte-identical.
- [x] 🤖 **Dirty-frame render skip (R4) -- IMPLEMENTED, VALIDATED,
      PARKED as a negative result (2026-07-10, branch `perf/r4-dirty-frame`
      `3327797`, NOT merged)**. Whole-frame skip when the render signature
      (FNV over OAM + all render control regs, plus vramGen/cgramGen) is
      unchanged and no raster hazard (no visible-line ppu_write last frame,
      no HDMA armed). Correct: per-frame fb CRCs byte-identical to no-skip
      across all 11 fixtures x 300 frames; field device build shows exact
      no-regression. BUT it fires ~0% on every real-content scene: the
      skip only triggered on the degenerate black fixtures (004/001 render
      all-zero). Every scene that draws real pixels animates each frame --
      palette cycling (title crystal, field torches/reflections: cgram
      changes every frame) or raster splits (dialogue/combat/worldmap:
      BG scroll written mid-frame, e.g. 013 writes $2111/$2112 at vPos
      19 and 84). The load-bearing assumption (frame-identical periods in
      rendered scenes) does not hold for FF4. Parked; the signature/raster/
      HDMA gate machinery is sound and reusable if a future need arises.
- [x] 🤖 **Field map-engine porting campaign, batches 1-2 + the honest
      measurement (2026-07-10)**: 4 routines ported L2 (D00BDB2
      CalcObjScreenPos 28/frame; D00C2FF/D00C347/D00C357 npc-map cluster
      ~32/frame) -- miss rate on 009 halved (94.3% -> 44.4%). Device D6
      A/B (field 009, frameskip 3, savestate-boot): emu 31.61 -> 31.33
      ms/frame (-0.9%). SECOND confirmation of the 2026-07-06 lesson:
      dispatch call-rate is not time -- the eliminated leaves were tiny
      (~2.4k opcodes/frame). Porting leaf JSRs improves coverage and
      correctness posture but is NOT a framerate lever; moving field emu
      meaningfully means porting whole subtrees (movement/NPC main-loop
      bodies) or the remaining machinery/APU levers. Campaign continues
      as a correctness/coverage track, decoupled from perf expectations.
      Next targets mapped: $00:9FC2 (10/frame, FOURTH disassembly
      off-by-2 verified by ROM bytes, JMP $9FF3 continuation to trace),
      dead-entry requalification 0x1E9F6C (UpdateLocalTiles_c: rewritten
      bank + off-by-2 -> likely never hits).
- [x] 🤖 **Palette-only partial skip (R5) — DONE, measured, merged
      (2026-07-10, ff4-gnw `613146c`)**: geometry stable + cgram animated
      → reuse decode+compose from a per-line store (~143 KB overlay),
      re-run only the output stage. Title coldboot skip-3 A/B: render
      −36% (render-portion −64%), emu unchanged, title 23.9 → 28.1 fps.
      Byte-identical (82/82 deep). Fires where R4 could not (title
      299/300, field 261/300). R4 whole-frame skip kept as mode 1.
- [x] 🤖 **R5 store vs FF4_LOAD_SAVESTATE — RESOLVED (2026-07-10,
      ff4-gnw `e4c93d2`)**: the combination missed the RAM_EMU budget by
      only 2,676 bytes; halving the R2b tile-row cache (4096 -> 2048
      slots, power of two kept) freed 32 KB. Byte-identical revalidated
      (41/41 vs the R5 goldens — collisions only re-decode). Both
      configs now clean-link; R5+savestate flashed and live on device
      (airship state loads, frames advance).
- [ ] 🤖 **(superseded spec kept for reference) Palette-only partial skip (the ACTUAL lever the R4 diagnosis
      exposed, sizable)**: when ONLY cgram changed (title/field palette
      animation -- the dominant real-scene case), decode (~17 ms) and
      compose (~10 ms) are identical frame-to-frame; only the output-stage
      palette differs (already cached by R2a). Reusing the previous
      frame's composed line result and re-running only the output stage
      would cut ~27 of the ~62 ms -- plausibly 60 fps on the title.
      COST/BLOCKER: needs the composed result of all 224 lines stored
      (s_lrPix+s_lrLayer, ~114-170 KB depending on packing) against a
      ~143 KB overlay margin -- tight, needs a packing scheme (uint8
      indices for <=8bpp, directColor fallback) and careful validation.
      Dedicated session. Byte-identical bar (R2a already proves the
      palette re-application is exact).
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
