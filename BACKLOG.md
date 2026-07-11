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
      bank + off-by-2 -> likely never hits). Both done in batch 3, below.
- [x] 🤖 **Field map-engine porting campaign, batch 3 (2026-07-11)**:
      both mapped targets landed. D009FC2 GetTileProps L2 (tile-properties
      leaf, ~10/frame; the JMP $9FF3 "continuation" turned out to be an
      internal jump to the routine's own tail -- fourth off-by-2). The
      0x1E9F6C dead entry was CONFIRMED dead (rewritten bank + off-by-2:
      $1E:9F6C is data, zero call sites in the whole ROM; its "hardcore
      PASS" was vacuous -- the old spike ran the asm side at data bytes
      and the production get_tile_prop_emu helper was a weak no-op) ->
      retired, and UpdateLocalTiles rewritten dp-relative at the real
      $00:9F6E (fifth off-by-2), its five inner calls now hitting the
      native GetTileProps_c. Spikes 5000/0 both; in-game 009 FB/OAM
      byte-identical, misses 9000 -> 8400/300f, verdicts unchanged 7/7.
      Correctness/coverage track as decided -- no perf claim. TOOLING
      SHARP EDGE surfaced: generate_spike.py resolves the spike target
      from the port FILE stem via ca65-bridge and trusts it over the
      REVERSED_FUNCTION line -- on off-by-2 routines the bridge returns
      the annotated WRONG address (4975/5000 fails, asm side executing
      mid-instruction garbage). Workaround: name the port file so the
      bridge can't resolve it (UpdateLocalTilesEntry.c). A proper
      trust-the-contract override directive is a candidate small fix.
- [x] 🤖 **Palette-only partial skip (R5) — DONE, measured, merged
      (2026-07-10, ff4-gnw `613146c`)**: geometry stable + cgram animated
      → reuse decode+compose from a per-line store (~143 KB overlay),
      re-run only the output stage. Title coldboot skip-3 A/B: render
      −36% (render-portion −64%), emu unchanged, title 23.9 → 28.1 fps.
      Byte-identical (82/82 deep). Fires where R4 could not (title
      299/300, field 261/300). R4 whole-frame skip kept as mode 1.
- [x] 🤖 **R6 — mosaic on the line-renderer fast path (2026-07-10,
      ff4-gnw `a5dbc86`, merged)**: pixelation transitions (battle entry,
      teleports) used to be rejected by ppu_lrFastPathOk and fall back to
      the legacy per-pixel renderer — the direct cause of the
      player-reported "pixelation is super slow". Mosaic is
      line-renderer-friendly (base-row decode + per-block horizontal
      replication, same signed-% expression as legacy). Byte-identical on
      the mosaic fixtures (005: 12k lines, 012: 7k) + full sweep 41/41;
      mosaicStartLine added to the R4/R5 signature. Desktop transition
      window −28% on x86; M7 larger.
- [x] 🤖 **R10 — packed-word final palette (2026-07-11, ff4-gnw `a281f8b`,
      merged) + the honest measurement correction**: s_lrPal4 (one LE word
      per color, pixelOutputFormat baked in, pad byte written as the 0 it
      always contains and that no reader observes) turns every whole-line
      output path (m7 fused x2, generic fast path, R5 palette replay)
      into one word load + one word store per pixel. DTCM balanced by
      evicting s_m7Line (pal4 = pal3 + 256 B; the boundary wall). ALSO:
      per-SECTION map attribution (using -ffunction-sections .text.*
      entries instead of global symbols) dissolved the phantom
      \"input_read 17%\" bucket -- it was ppu_runLine's inlined body all
      along; real post-M2 shares: render ~52%, interpreter ~20%, APU
      ~12%, blit+libc ~11%. Validation: 9/9 CRCs, 1000f long-horizon,
      verdicts 7/7, device link pre-verified. MEASUREMENT CORRECTION
      (applies to R8b/R9 claims too): repeated aligned-window device
      readings vary +/-1.5 fps -- R8b/R9/R10 are individually SUB-NOISE
      on device (desktop shows the real structural chain: M2 0.27 ->
      R9 0.24 -> R10 0.23 s per 600 frames on 008). The M7's store
      buffer already merged the byte stores; its render bottleneck is
      VRAM/AXI fetch latency, not stores. CONCLUSION: the render
      micro-opt series is exhausted; remaining levers are the
      interpreter (worldmap subtree dispatch -- a decompilation
      campaign, not a renderer patch), the APU (~12%, human call), and
      better device metrology first (a deterministic per-300-frame D6
      block ring readable via gdb would replace the noisy wall-clock
      windows).
- [x] 🤖 **R9 — per-frame sprite line-coverage map (2026-07-11, ff4-gnw
      `a22c86a`, merged, device-measured)**: evaluateSprites scanned all
      128 OAM entries per line (224x/frame) just to find y-range members;
      a lazily-rebuilt 256-bit coverage map (exact same membership
      formula; invalidated on OAM/high-OAM/OBSEL/SETINI writes, reset,
      savestate load) skips scan AND memset on provably-empty lines
      (~80% on the worldmap). Covered lines run the original evaluator
      unchanged. The first cut indexed OAM per-sprite instead of
      per-WORD-pair and failed 5/9 CRC fixtures -- proof the battery
      exercises sprite coverage. Validation: 9/9 CRCs vs R8b, 1000f
      long-horizon x2, verdicts 7/7, device link pre-verified. Device
      (aligned window): 27.6 -> 27.8 fps -- noise-level; the OAM scan is
      cheaper on the M7 than estimated (linear, cache-friendly).
      Structural saving on every scene, but the render residual is now
      dominated by the fused decode/output loops themselves. NEXT LEVERS
      by measured share: the unidentified input_read map-bucket (~17%
      post-M2 -- resolve its real content first), interpreter residual
      (~17%: worldmap subtree dispatch or vblank-spin extension), APU
      (~8%, human call).
- [x] 🤖 **R8b — mode-7 sprite lines fused too (2026-07-11, ff4-gnw
      `15544dd` + DTCM fix `1dfe19a`, merged, device-measured)**: the ~20%
      of mode-7 lines carrying sprites still ran the generic pipeline.
      actMode 7's five compose passes collapse to one per-pixel select
      (opaque un-masked sprite wins unless prio 0 over opaque BG).
      Engagement lesson RE-CONFIRMED: FF4 windows the SPRITE layer exactly
      like the BG (inverted [1,254] edge mask), so a !windowed gate on
      layer 4 sent every sprite line straight back to the generic path --
      counters caught it, the window is applied as a span mask inside the
      select instead. With it: ZERO generic mode-7 lines on 008. Also hit
      a hard wall: .ff4_dtcm is within 16 BYTES of a fixed LD boundary --
      s_m7Win went to plain overlay BSS (any future DTCM scratch needs
      that budget check first). Validation: FB CRCs 9/9 vs M2 binary,
      1000f long-horizon identical, oracle verdicts 7/7. Device
      (aligned-window A/B, host 536-856): 26.9 -> 27.6 fps (+2.6%,
      scene-noise adjacent but structurally strictly less work/line).
      DAY TOTAL worldmap 008: 7.3 -> 27.6 fps (x3.8).
- [x] 🤖 **M2 — wait-spin fast-forward (2026-07-11, ff4-gnw `43b77b3`,
      merged, device-measured)**: a PC histogram (new FF4_PC_PROFILE tool
      in cpu.c) showed 67% of ALL interpreted opcodes on 008 inside two
      2-instruction WaitVblank loops ($00:9133/$00:9142 -- annotated two
      bytes off in the disassembly, as usual). Such \`lda dp / bne -4\`
      loops write nothing, so they only exit via an interrupt: while none
      fires, every iteration is state-identical at the loop head. The
      fast-forward (hooked on taken -4 branches, self-verifying pattern +
      state/cost calibration over two iterations) advances the CLOCK ONLY
      in whole-iteration chunks and stops short of the NMI-set tick; the
      interpreter runs the last real iterations so NMI vectoring is
      cycle-exact. Sharp edges that each produced (or would have produced)
      real divergence: chunks capped under one scanline (one +40 DRAM
      refresh per hPos-536 crossing, like real execution); under active
      HDMA the horizon stops short of each h==1104 arming tick so the
      crossing iteration drains at the exact access cadence (the worldmap
      spin RUNS with HDMA armed -- a binary HDMA gate would have killed
      the whole win); at exactly hPos==1104 the arming event has NOT run
      yet -- distance 0, not a full line (this one shipped briefly and
      produced sporadic frame diffs from frame 229 of 008 before the
      engagement-counter methodology caught... the CRC battery caught it;
      fixed). Desktop: interpreted opcodes 4.18M -> 1.87M (-55%) on 008.
      Validation: FB CRCs identical vs R8 on 9 fixtures, 1000-frame
      long-horizon FB+WRAM identical (008, 009), oracle verdicts 7/7 (the
      oracle's pure-interpreter pass itself runs with M2 active). Device
      D6 (008, skip 0, same-day): 23.5 -> 26.9 fps (+14%), 41.5 -> ~37
      ms/frame; post-M2 profile: CPU-interpreter buckets ~33% -> ~17%,
      render back to lever #1 (~40% incl. per-line evaluateSprites and
      the ~20% sprite lines still on the generic path). Residual spin in
      vblank (gate) is small and left for later. DAY TOTAL on worldmap
      008: 7.3 -> 26.9 fps (x3.7).
- [x] 🤖 **R8 — specialise and fuse the mode-7 line pipeline (2026-07-11,
      ff4-gnw `45739e4` + `78078d6`, merged, device-measured)**: census of
      FF4's real mode-7 usage (008/011/012) showed pure uniform scale
      (m7matrix[1]=[2]=0 -- no rotation, one map row per line), no
      flips/largeField/mosaic/math/dc, clip 0, ~80% sprite-free lines.
      Three byte-identical changes: (1) HOT decode variant -- incremental
      accX (no per-pixel multiply), hoisted row bases, tilemap fetch
      memoised per tile column, explicit LE byte loads; (2) fused
      decode->output for the dominant line -- out = pal3[pixel] directly
      (backdrop == pal3[0]), R5 store written in place, skipping window
      build + compose + generic output; (3) brightness LUT cached
      (was 32 muls+divides per line x224). TRAP worth remembering: FF4's
      worldmap runs layer 0 main-screen-WINDOWED (inverted window1
      [1,254] masking only columns 0/255 -- the mode-7 edge-artifact
      hide); the first fused gate required !windowed and therefore NEVER
      engaged -- caught by instrumented engagement counters, not by the
      CRC battery (which passed vacuously on the unexercised path); fixed
      by span-masking the decoded line (ppu_lrWinMaskU8). Validation:
      FB CRCs identical vs R7 on 9 fixtures (fused live, ~78% of 008's
      m7 lines), oracle verdicts 7/7. Device D6 (008, skip 0, same-day):
      emu+render 53.7 -> 41.5 ms/frame (-23%), fps 18.4 -> 23.5 (+28%);
      cumulative over the day 139.9 -> 41.5 (x3.4), fps 7.3 -> 23.5
      (x3.2). Post-R8 profile: emu ~33% is now lever #1 (M2 vblank-spin
      fast-forward / worldmap dispatch), render bucket ~32% (incl.
      per-line ppu_evaluateSprites), APU ~12%.
- [x] 🤖 **R7 — mode 7 on the line-renderer fast path (2026-07-11, ff4-gnw
      `45dc9da`, merged; device flash pending)**: the direct product of the
      D6/PC-profile read below. ppu_lrDecodeM7Line reproduces the legacy
      affine walk per pixel and feeds the hoisted compose/output stages;
      m7startX/Y computed ahead of the row clamp so the savestate/signature
      state matches legacy exactly; EXTBG implemented but gated off the
      fast path (zero actMode-9 lines in any fixture -- ships unreachable
      rather than unvalidated). Byte-identical FB CRCs vs the parent
      binary: 008 (~50k mode-7 lines/300f), 011 (~70k), 012, + five
      non-mode-7 fixtures; coverage instrumented before being claimed (R6
      lesson); oracle verdicts unchanged 7/7. Desktop wall-clock whole-run:
      008 -43%, 011 -58%. **DEVICE-MEASURED same day (D6 same-day-reflash
      A/B, M3 method, 008-overworld-mode7 savestate-boot -- baked
      savestate switched from 013 to 008 at Hoani's call, 013 exercises
      zero mode-7 lines at its start -- frameskip 0)**: emu+render 139.9
      -> 53.7 ms/frame (-62%), fps 7.3 -> 18.4 (x2.5), blit 2.0 unchanged.
      Post-R7 profile on the flight scene: ppu_runLine 40% (the affine
      walk is inherently per-pixel -- no tile spans -- so mode-7 lines
      keep a higher floor than modes 0/1/3), CPU interp ~25%, APU ~10%.
      Observation-channel caveat logged: SWD reads of once-written cached
      state (ff4_snes pointer, LCD framebuffers) can return stale zeros
      through the M7 D-cache -- use per-frame-written counters (D6,
      g_diag_host_frame) as the liveness/measurement channel, not
      pointer-chased struct reads.
- [x] 🤖 **D6 read on the live R5+R6 firmware (2026-07-11, airship/worldmap
      mode-7 state, frameskip 0, probe attach without reflash)**: at skip 0
      D6 cannot split emu from render (emu_ms=0 by construction; rend_ms
      carries both) -- 250 frames over a 20 s window: emu+render
      78.9 ms/frame, blit 2.0 ms, ~12.4 fps (liveness cross-check 13.3).
      PC-sampling profile instead (150 probe samples; `flushregs` after
      every halt is MANDATORY -- without it gdb's register cache returns
      the same stale PC 150/150): ppu_runLine 47.3% + memset (compose /
      objPixelBuffer clears) 5.3% -> render ~53%; CPU interpreter
      (runCycles/cpuRead/cart_write/runOpcode/runFrame) ~25%; APU/DSP ~9%;
      input_read (LakeSnes auto-joy shift register; bucket may absorb
      following statics -- map-level symbols only) 9.3%; app_main 3.3%.
      ROOT CAUSE of the render share: ppu_lrFastPathOk accepts only modes
      0/1/3, so MODE 7 scenes run the legacy per-pixel renderer -- same
      structural story as pre-R6 mosaic. VERDICT for the pending decision:
      on mode-7 scenes the renderer still dominates (~53% vs ~34%
      emu+APU); lever #1 there is a mode-7 line-renderer fast path ("R7",
      analogous to R6) or the M1 structural work -- NOT continued
      dispatch. Scene-specific caveat: field/title (modes 0/1) already run
      the fast path; re-profile those before generalizing.
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
