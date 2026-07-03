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
- [ ] 🤖 `gen_dispatch.py` — move the manual table edits into it
      (inline TODO in `dispatch_all.c`)

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

---

**Legend**: 🤖 doable by agent · 🧑 requires the human (hardware, push,
decision). `[x]` = done · `[ ]` = to do.
