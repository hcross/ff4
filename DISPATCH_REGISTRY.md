# FF4 → G&W Dispatch Registry

> **Living** registry of the ported and dispatched routines. Source of truth on
> the identity, role, and maturity of each dispatch. ID convention and maturity
> scale defined in [AGENTS.md](AGENTS.md) §B.1 / §B.2.

**ID convention**: `D<bank><addr>` (6 uppercase hex digits of the SNES PC).
**Scale**: `L0` stub · `L1` ported, unproven · `L2` runtime equivalence (spike) ·
`L3` oracle validation (`wram_diff=0`) · `L4` device-tested ·
`EXCL` intentional DMA-bypass (off-scale) ·
`DELEG` delegate wrapper (executes the asm via `run_emulated_func` — equivalent by
construction, but not a native port: no perf gain).

## Audit methodology

**Evidence-based** levels: hardcore_log PASS, KNOWN_FINDINGS (`wram_diff=0`),
F10/F12 fixes, excluded DMA-bypasses, then L1→L2 promotion via
`translator/batch_spike_ffgnw.py` — fuzzed spike on the `ff4-gnw` bodies vs
interpreted asm (`fails==0` ⇒ L2). The initial "build_error" catch-all was
broken down and then resolved: delegate→DELEG, run_hang (false hangs = compound
budget, rerun with reduced budget → L2), parser_error (hardened parser → L2),
leaving 2 compile_error (inter-routine dependency / include).

> **Scope of L2-by-spike**: equivalence of the observable slot under fuzzing of
> the CONTRACT inputs — strong but **not exhaustive**. Stronger than L1, less
> isolated than L3 (in-game oracle). **FAILs** = real divergences to investigate (WF-VALID).

<!-- REGISTRY:DISTRIBUTION:START -->
**Distribution** (generated from `registry/dispatch_state.jsonl` — do not hand-edit; edit the JSONL via `registry/registry_promote.py` and re-run `python registry/render_registry.py`): L0=1 · L1=16 · L2=165 · L3=7 · EXCL=3 · DELEG=12 · RETIRED=2 (total 204).
<!-- REGISTRY:DISTRIBUTION:END -->
`ExecBtlGfx` (D038085) REMOVED from the dispatch on 2026-06-30 (206→205): BLOCKING
animation (multi-frame WaitVblank/WaitFrame) incompatible with the synchronous
run_emulated_func → ~1s freeze (50M guard) + premature end of battle; must remain
interpreted. ROOT cause of all battle bugs (SDL-validated). Category: routine with
Wait* = never dispatched.
The 23 L1: 11 `no_source` (bundled btlgfx → custom spike), 8 `no_contract`
(CONTRACT to be written), 2 `fail` (`CheckMenu_c`, `TfrBGAnimGfx_c` → WF-VALID),
2 `compile_error` (`RandXA_c` dep. `Div16_c`; `TfrVRAM_c` include). Cf.
[BACKLOG](BACKLOG.md) §3.

> 🩹 **False-L2 repaired (2026-06-29).** `D00834E InitMapRAM_c` was L2 (spike
> PASS) but wrote to the zero-page WRAM (`$00/$01/$02`) instead of the MMIO
> registers `$2100/$420C/$4200` → corrupted mode-7. The spike only checked
> `output_ram 0x06FB` and missed the MMIO effect. **Lesson: the CONTRACT must
> declare MMIO effects as `output_ram`, otherwise the spike yields a false L2.**
> Fixed (snes_write), oracle-validated (FB-clean) + visually. **2nd identical
> case: `D15B143 TfrBGGfx_c`** (bug 4, corrupted tiles) — wrote the DMA registers
> to WRAM `$43xx` instead of the bus; false-L2 for the same reason (the CONTRACT
> listed `$43xx` as WRAM). Difference: it is a **DMA** → the `snes_write`
> translation does not flush from the isolated dispatched C (class F6), so it is
> interpreted on desktop; a device-correct port requires a manual VRAM loop.

> ⚠ **Battle graphics cluster — integration divergence CONFIRMED (2026-06-28).**
> Oracle bisection (006-in-combat): `03FE03 028560 0285D2 0290A0 02A491 02BB0B
> 02BB1A 02DA73 02DAFE 02DCED 02DDA5 02DDDC 03805F 038085` cause the **battle
> render + flickering menu** glitches (all disappear in the interpreter). Ported
> as a block (`eee0a51`), **never validated** (no_source / bundled). The
> single-slot spike does not catch them — proof that **L2-spike ≠ correct
> render**. Desktop workaround: `main_sdl.c host_exclude_combatgfx` (interprets
> them, device intact). True device fix = **repair** the cluster (porting debt).

---

## Table 1 — Decompilation & maturity

<!-- REGISTRY:TABLE1:START -->
| ID | SNES Address | C Routine | Domain | Level | Proof / notes |
|----|--------------|-----------|--------|-------|---------------|
| `D00808E` | $00:808E | `AfterBattle_c` | field | L2 | fuzzed spike, 0 fails |
| `D0080A0` | $00:80A0 | `FieldMain_c` | field | L2 | fuzzed spike, 0 fails |
| `D0081F4` | $00:81F4 | `CheckMenu_c` | field | L1 | spike: 1/200 fails — divergence (WF-VALID) |
| `D008302` | $00:8302 | `UpdatePlayerSpeed_c` | field | L2 | fuzzed spike, 0 fails |
| `D00834E` | $00:834E | `InitMapRAM_c` | field | L3 | mode-7 MMIO fix (1a86d23) — oracle FB-clean; ex-false-L2 (spike missed the MMIO effect) |
| `D00883D` | $00:883D | `_00883d_c` | field | L1 | no CONTRACT block |
| `D00885E` | $00:885E | `_00885e_c` | field | L1 | no CONTRACT block |
| `D00AA58` | $00:AA58 | `CheckTilePass_c` | field | L2 | fuzzed spike, 0 fails |
| `D00AAD8` | $00:AAD8 | `SetPlayerNPCMap_c` | field | L1 | no CONTRACT block |
| `D00AB13` | $00:AB13 | `ClearPlayerNPCMap_c` | field | L2 | fuzzed spike, 0 fails |
| `D00AC7D` | $00:AC7D | `CheckVehicleBlock_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D00BE47` | $00:BE47 | `CalcVehicleSpritePos_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D00C0C4` | $00:C0C4 | `PlayerSpriteTiles_c` | field | L2 | fuzzed spike, 0 fails |
| `D00C3BD` | $00:C3BD | `UpdateWhalePal_c` | field | L2 | fuzzed spike, 0 fails |
| `D00CB5F` | $00:CB5F | `TfrBGAnimGfx_c` | field | L1 | spike: 2/200 fails — divergence (WF-VALID) |
| `D00F533` | $00:F533 | `UpdateBG2Scroll_c` | field | RETIRED | dead entry -- $00:F533 is not an instruction boundary (mid-operand byte of the preceding routine's LDX $43 at $00:F532; $00:F534=RTS), confirmed by direct ROM inspection. Never a valid call target. The disassembly's two-entry model (F533=full/F535=skip) was off by 2 bytes; see D00F535 for the real, sole entry point. Retired 2026-07-05. |
| `D00F535` | $00:F535 | `UpdateBG2ScrollSkip_c` | field | L2 | FIXED: guard source was cpu->a (wrong), changed to ram[dp+0xC9] matching the real $00:F535 asm (LDA $C9), confirmed by direct ROM-byte inspection. Dead sibling entry D00F533 retired same day. Region-compare spike 5000/5000 pass. (evidence: ff4-port/translator/runs/D00F535_updatebg2scrollskip_FIXED_revalidation.txt) |
| `D00FFBC` | $00:FFBC | `InitCharProp_ext_c` | field | L2 | hardcore PASS |
| `D00FFE0` | $00:FFE0 | `Vectors_c` | field | L2 | fuzzed spike, 0 fails |
| `D018010` | $01:8010 | `UpdateCtrlField_ext_c` | menu | L2 | hardcore PASS; input reimpl. (F5) |
| `D01CA85` | $01:CA85 | `TfrVRAM_c` | field | L1 | spike does not compile (inter-routine dependency / include) |
| `D01D718` | $01:D718 | `FadeIn_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D01DFD2` | $01:DFD2 | `LoadBattleSpeedPosText_c` | menu | L2 | hardcore PASS |
| `D028560` | $02:8560 | `Mult8_btlgfx_c` | btlgfx | L2 | Bundled-body routine (btlgfx_prim.c). Extracted verbatim to port/btlgfx/Mult8_btlgfx.c; body already correct (no fix needed — bit-serial ROR/ADC loop, no 8-bit ASL-index truncation class applies). Fixed output_ram 0x2A=2 (16-bit product 2A:2B). Spike 300 trials, 0 fails. (evidence: ff4-port/translator/runs/D028560_mult8_btlgfx_revalidation.txt) |
| `D0285D2` | $02:85D2 | `HardMult_btlgfx_c` | btlgfx | L2 | Extracted MultHW ($02:85D2) from bundled btlgfx_prim.c into port/battle/HardMult_btlgfx.c; standalone spike 300/300 pass, 0 fails. Body verbatim (hardware 8x8->16 multiply ram[$1C]*ram[$1E]->ram[$20:$21]); no bug found, no width-truncation risk (8x8->16 fits uint16_t). (evidence: ff4-port/translator/runs/D0285D2_hardmult_btlgfx_revalidation.txt) |
| `D0290A0` | $02:90A0 | `TfrBG2MenuTile_c` | btlgfx | L1 | no CONTRACT block |
| `D02A491` | $02:A491 | `IncrTextPtr_c` | btlgfx | L2 | Extracted bundled body (btlgfx_prim.c) to standalone port/btlgfx/IncrTextPtr.c; 16-bit X increment, no truncation bug (verbatim body already correct); auto-spike 300 trials, fails: 0 (evidence: ff4-port/translator/runs/D02A491_incrtextptr_revalidation.txt) |
| `D02BB0B` | $02:BB0B | `BackAttackYOffset_s_c` | btlgfx | L1 | non-standalone body (bundled btlgfx) |
| `D02BB1A` | $02:BB1A | `BackAttackYOffset_l_c` | btlgfx | L1 | non-standalone body (bundled btlgfx) |
| `D02DA73` | $02:DA73 | `DrawMonsterSprite_c` | btlgfx | L2 | region-compare spike (SPIKE_MASK 0x1C-0x1D), 300/300 pass, re-verified 2026-07-05 — extraction PoC dated 2026-06-30 (ff4-port ba9b3d8/3e388bc) never promoted (evidence: ff4-port/translator/runs/D02DA73_drawmonstersprite_revalidation.txt) |
| `D02DAFE` | $02:DAFE | `InitMonsterAnim_c` | btlgfx | L2 | Extracted InitMonsterAnim_c standalone (btlgfx_monsters.c), region spike 300/300 fails:0; mutation-verified teeth (write-path mutation -> 296/300 fails). Applied 8-bit index-truncation fix on mon47<<2 in ff4-gnw too (benign for 0..5 slots, faithful to asm). headless-all builds clean. (evidence: ff4-port/translator/runs/D02DAFE_initmonsteranim_revalidation.txt) |
| `D02DCED` | $02:DCED | `BuildOAMEntries_c` | btlgfx | L2 | fixed y_row 8-bit truncation bug (diverged for slot>=64, latent since 2026-06-30), region-compare spike 300/300 pass after fix, re-verified 2026-07-05 (evidence: ff4-port/translator/runs/D02DCED_buildoamentries_revalidation.txt) |
| `D02DDA5` | $02:DDA5 | `CheckSpriteVisible_c` | btlgfx | L2 | Extracted verbatim from btlgfx_monsters.c into translator/port/battle/CheckSpriteVisible.c; region spike 300/300 pass (ram$64 parity + no stray WRAM writes, $0E scratch masked). Carry-flag output not spike-observable; carry equivalence per prior whole-game oracle (ff4-port-frame26-debug, 2026-06-24). (evidence: ff4-port/translator/runs/D02DDA5_checkspritevisible_revalidation.txt) |
| `D02DDDC` | $02:DDDC | `UpdateMonsterAnim_c` | btlgfx | L1 | non-standalone body (bundled btlgfx) |
| `D038009` | $03:8009 | `ExecBattle_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03805F` | $03:805F | `DrawMP_c` | battle | L2 | fuzzed spike, 0 fails |
| `D038085` | $03:8085 | `ExecBtlGfx_c` | battle | RETIRED | BLOCKING animation (Wait*) — removed from the dispatch 2026-06-30, must remain interpreted (cf. distribution above) |
| `D0382CB` | $03:82CB | `InitHWRegs_c` | field | L3 | wram_diff=0 verified + hardcore PASS |
| `D038379` | $03:8379 | `RandXA_c` | battle | L1 | spike does not compile (inter-routine dependency / include) |
| `D0383B9` | $03:83B9 | `Mult16_c` | battle | L3 | wram_diff=0 verified (oracle artefact) |
| `D0383E0` | $03:83E0 | `Mult8_c` | battle | L2 | fuzzed spike, 0 fails |
| `D038407` | $03:8407 | `Div16_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0384E3` | $03:84E3 | `Add16_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0384FC` | $03:84FC | `Sub16_c` | battle | L2 | fuzzed spike, 0 fails |
| `D038579` | $03:8579 | `RandMonster_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03858B` | $03:858B | `Rand99_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03859B` | $03:859B | `AddMsg1_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0385A6` | $03:85A6 | `AddMsg2_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0385B1` | $03:85B1 | `AddMsg3_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0387D8` | $03:87D8 | `CheckFanfare_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0387E4` | $03:87E4 | `CheckBattleList_c` | battle | L2 | fuzzed spike, 0 fails |
| `D038803` | $03:8803 | `CheckWinAnim_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0395CE` | $03:95CE | `InitCharRows_c` | battle | L3 | wram_diff=0 verified (oracle artefact) |
| `D039741` | $03:9741 | `GetPendingAction_c` | battle | L2 | fuzzed spike, 0 fails |
| `D039788` | $03:9788 | `CheckTimer_c` | battle | L2 | fuzzed spike, 0 fails |
| `D0397B3` | $03:97B3 | `InitAction_c` | battle | L2 | F12 — functional in-game equivalence |
| `D039E65` | $03:9E65 | `TimerDur_00_c` | battle | L2 | fuzzed spike, 0 fails |
| `D039E71` | $03:9E71 | `TimerDur_02_c` | battle | L2 | fuzzed spike, 0 fails |
| `D039F1C` | $03:9F1C | `TimerDur_08_c` | battle | L2 | fuzzed spike, 0 fails |
| `D039F75` | $03:9F75 | `TimerDur_0a_c` | battle | L2 | fuzzed spike, 0 fails |
| `D039FD8` | $03:9FD8 | `ApplySpeedMod_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03B33F` | $03:B33F | `Cmd_21_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BA04` | $03:BA04 | `AITarget_1e_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BA67` | $03:BA67 | `AITarget_1f_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BA74` | $03:BA74 | `AITarget_20_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BA81` | $03:BA81 | `AITarget_21_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BA8E` | $03:BA8E | `AITarget_22_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BAEF` | $03:BAEF | `AITarget_23_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BAFE` | $03:BAFE | `AITarget_24_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BB0D` | $03:BB0D | `AITarget_25_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BB6B` | $03:BB6B | `AITarget_29_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BDA9` | $03:BDA9 | `AICond_02_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BE1E` | $03:BE1E | `AICond_05_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BE31` | $03:BE31 | `AICond_06_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BEE4` | $03:BEE4 | `AICond_09_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BF05` | $03:BF05 | `AICond_0b_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03BFF6` | $03:BFF6 | `AICondTarget_25_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03C03B` | $03:C03B | `AICondTarget_26_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03C042` | $03:C042 | `AICondTarget_27_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03C049` | $03:C049 | `AnyTarget_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03C06C` | $03:C06C | `AICondTarget_23_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03C987` | $03:C987 | `CalcHits_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03D378` | $03:D378 | `MagicDmgEffect_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03D466` | $03:D466 | `MagicEffect_04_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03D613` | $03:D613 | `MagicEffect_08_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03D83F` | $03:D83F | `MagicEffect_0d_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03D863` | $03:D863 | `MagicEffect_0e_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03D972` | $03:D972 | `MagicEffect_13_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03D9EC` | $03:D9EC | `MagicEffect_15_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DA0C` | $03:DA0C | `MagicEffect_16_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DC9B` | $03:DC9B | `MagicEffect_20_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DCBB` | $03:DCBB | `MagicEffect_21_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DCD6` | $03:DCD6 | `MagicEffect_22_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DD06` | $03:DD06 | `MagicEffect_24_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DD65` | $03:DD65 | `MagicEffect_2c_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DD95` | $03:DD95 | `MagicEffect_28_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DDB1` | $03:DDB1 | `MagicEffect_2a_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DDC9` | $03:DDC9 | `MagicEffect_2b_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DDDD` | $03:DDDD | `MagicEffect_2f_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03DFD2` | $03:DFD2 | `MagicEffect_32_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03E030` | $03:E030 | `RemoveTarget_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03E100` | $03:E100 | `CheckStrongElem_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03E133` | $03:E133 | `CheckWeakElem_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03E43B` | $03:E43B | `Cmd_22_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03E4D9` | $03:E4D9 | `TwinFailed_c` | battle | L2 | fuzzed spike, 0 fails |
| `D03FE03` | $03:FE03 | `TfrSprites_c` | field | EXCL | F6 — manual OAM, excluded from baseline |
| `D048004` | $04:8004 | `ExecSound_ext_stub` | sound: | L0 | explicit no-op stub (F4) |
| `D0485E1` | $04:85E1 | `PlayGameSfx_c` | sound | L2 | fuzzed spike, 0 fails |
| `D04861E` | $04:861E | `ExecInterrupt_c` | sound | L1 | suspected false-L2: writes ram[0x2140..0x2143] directly instead of snes->apu->inPorts[X] (Pitfall 13); spike only compares declared output_ram so it cannot see this. Found by lint_ff4.py MMIO_IN_WRAM (2026-07-03). Entry-mode comment claims DB=$7E but ground-truth asm (sta hAPUIO0/1/2/3) implies DB must be $00 at this point for the routine to fulfil its documented purpose (SPC mailbox handshake) -- pending oracle confirmation, not yet proven at runtime. |
| `D088690` | $08:8690 | `LoadTitleGfx_c` | field | L1 | no CONTRACT block |
| `D08885E` | $08:885E | `TfrTitleCrystalTiles_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D0E8B3C` | $0E:8B3C | `CheckBattle_c` | field | L2 | hardcore PASS |
| `D12E35B` | $12:E35B | `WaitVblankEvent_c` | field | L2 | fuzzed spike, 0 fails |
| `D12E55A` | $12:E55A | `FindEventTerminator_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D12E613` | $12:E613 | `EventCmd_d8_c` | field | L2 | fuzzed spike, 0 fails |
| `D12E7D3` | $12:E7D3 | `EventCmd_d7_c` | field | L2 | fuzzed spike, 0 fails |
| `D12EB47` | $12:EB47 | `EventCmd_e0_c` | field | L2 | fuzzed spike, 0 fails |
| `D12EC06` | $12:EC06 | `EventCmd_e6_c` | field | L2 | fuzzed spike, 0 fails |
| `D12EC3E` | $12:EC3E | `EventCmd_dd_c` | field | L2 | fuzzed spike, 0 fails |
| `D12ED1D` | $12:ED1D | `SetCurrGil_c` | field | L2 | fuzzed spike, 0 fails |
| `D12EE1C` | $12:EE1C | `EventCmd_d0_c` | field | L2 | fuzzed spike, 0 fails |
| `D12EE25` | $12:EE25 | `EventCmd_d1_c` | field | L2 | fuzzed spike, 0 fails |
| `D12EE35` | $12:EE35 | `TfrInvertPal_c` | field | L2 | fuzzed spike, 0 fails |
| `D13BFE3` | $13:BFE3 | `_00bfe3_c` | field | L2 | fuzzed spike, 0 fails |
| `D13C11F` | $13:C11F | `ReloadNPCs_c` | field | L2 | fuzzed spike, 0 fails |
| `D13D730` | $13:D730 | `LoadTheEndGfx_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13DB10` | $13:DB10 | `_13db10_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13DB23` | $13:DB23 | `_13db23_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13E07D` | $13:E07D | `_13e07d_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13E139` | $13:E139 | `GetEarthSpritePos_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13E247` | $13:E247 | `InitStars_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13E2DC` | $13:E2DC | `GetOtherPlanetTile_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13E512` | $13:E512 | `Mult16_1_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13EB24` | $13:EB24 | `NewLine_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13EB60` | $13:EB60 | `_13eb60_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13EBB8` | $13:EBB8 | `_13ebb8_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13EF4C` | $13:EF4C | `_13ef4c_c` | cutscene | L2 | fuzzed spike, 0 fails |
| `D13FE36` | $13:FE36 | `AutoBattle_0003_c` | battle | L2 | fuzzed spike, 0 fails |
| `D14F58E` | $14:F58E | `_14f58e_c` | field | L2 | fuzzed spike, 0 fails |
| `D14F626` | $14:F626 | `GilWindowTiles3_c` | field | L2 | fuzzed spike, 0 fails |
| `D14F63E` | $14:F63E | `GilWindowTiles4_c` | field | L2 | fuzzed spike, 0 fails |
| `D14F6D6` | $14:F6D6 | `DlgTilesTop_c` | field | L2 | fuzzed spike, 0 fails |
| `D14F796` | $14:F796 | `MapTitleTilesTop_c` | field | L2 | fuzzed spike, 0 fails |
| `D14F7B6` | $14:F7B6 | `MapTitleTilesBtm_c` | field | L2 | fuzzed spike, 0 fails |
| `D14FA16` | $14:FA16 | `LavaAnimPal_c` | field | L2 | fuzzed spike, 0 fails |
| `D14FB1E` | $14:FB1E | `WipeScanlineTbl_c` | field | L2 | fuzzed spike, 0 fails |
| `D14FD00` | $14:FD00 | `InitCtrl_ext2_c` | menu | L2 | fuzzed spike, 0 fails |
| `D14FD03` | $14:FD03 | `UpdateCtrl_ext_c` | menu | L2 | fuzzed spike, 0 fails |
| `D14FD06` | $14:FD06 | `ClearText_ext_c` | menu | L2 | fuzzed spike, 0 fails |
| `D14FD09` | $14:FD09 | `UpdateWindowColor_ext_c` | menu | L2 | fuzzed spike, 0 fails |
| `D14FD0C` | $14:FD0C | `UpdateScrollRegs_ext_c` | menu | L2 | fuzzed spike, 0 fails |
| `D1585AB` | $15:85AB | `InitWorld_c` | field | L2 | fuzzed spike, 0 fails |
| `D1589ED` | $15:89ED | `InitInterrupts_c` | field | L2 | fuzzed spike, 0 fails |
| `D158B2A` | $15:8B2A | `InitDMA_c` | field | L2 | fuzzed spike, 0 fails |
| `D158D5D` | $15:8D5D | `PlayMapSong_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D158DFC` | $15:8DFC | `WaitKeyUp_c` | field | L2 | fuzzed spike, 0 fails |
| `D158E05` | $15:8E05 | `WaitKeyDown_c` | field | L2 | fuzzed spike, 0 fails |
| `D158E47` | $15:8E47 | `UpdateWaterLavaAnim_c` | field | L2 | fuzzed spike, 0 fails |
| `D158E57` | $15:8E57 | `TfrWaterLavaGfx_c` | field | L2 | fuzzed spike, 0 fails |
| `D158F34` | $15:8F34 | `TfrLavaGfx_c` | field | L2 | fuzzed spike, 0 fails |
| `D159104` | $15:9104 | `UpdateMode7Regs_c` | field | L2 | fuzzed spike, 0 fails |
| `D1591CA` | $15:91CA | `UpdateWipeIRQ_c` | field | L1 | no CONTRACT block |
| `D159204` | $15:9204 | `UpdateWipeNMI_c` | field | L2 | fuzzed spike, 0 fails |
| `D159792` | $15:9792 | `LoadPlayerGfxWorld_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D1597A2` | $15:97A2 | `LoadPlayerGfxSub_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D1599FB` | $15:99FB | `GiveGil_c` | field | L2 | fuzzed spike, 0 fails |
| `D159AE9` | $15:9AE9 | `GetTreasureTiles_c` | field | L2 | fuzzed spike, 0 fails |
| `D159B5B` | $15:9B5B | `GetTreasurePtr_c` | field | L2 | fuzzed spike, 0 fails |
| `D15AF24` | $15:AF24 | `CloseYesNoWindow_c` | field | L2 | fuzzed spike, 0 fails |
| `D15B09C` | $15:B09C | `ScrollItemListDown_c` | field | L2 | fuzzed spike, 0 fails |
| `D15B143` | $15:B143 | `TfrBGGfx_c` | field | L3 | bug 4 tiles RESOLVED: manual VRAM loop (c2fc6f1, F6 model) — true device+desktop fix, visually validated; native without exclusion |
| `D15B3DC` | $15:B3DC | `_15b3dc_c` | field | L1 | no CONTRACT block |
| `D15B41B` | $15:B41B | `GetDlgPtr1H_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D15B6F1` | $15:B6F1 | `InitDlgIRQ_c` | field | L2 | fuzzed spike, 0 fails |
| `D15B8C9` | $15:B8C9 | `_15b8c9_c` | field | L2 | fuzzed spike, 0 fails |
| `D15BB6A` | $15:BB6A | `_15bb6a_c` | field | L2 | fuzzed spike, 0 fails |
| `D15C144` | $15:C144 | `_15c144_c` | field | L2 | fuzzed spike, 0 fails |
| `D15C163` | $15:C163 | `_15c163_c` | field | L3 | F7 — diverges by 0 bytes |
| `D15C23D` | $15:C23D | `_15c23d_c` | field | L3 | wram_diff=0 verified |
| `D15C37F` | $15:C37F | `Pow10Hi_c` | field | L2 | fuzzed spike, 0 fails |
| `D15CA5E` | $15:CA5E | `_15ca5e_c` | field | EXCL | F11(KF) — palette DMA-bypass, excluded from baseline |
| `D15CA85` | $15:CA85 | `_15ca85_c` | field | L1 | no CONTRACT block |
| `D15CADC` | $15:CADC | `_15cadc_c` | field | EXCL | F3 — DMA-bypass, excluded from baseline |
| `D16C59A` | $16:C59A | `AfterCutscene_c` | field | L2 | fuzzed spike, 0 fails |
| `D16C8BC` | $16:C8BC | `Special_2d_c` | field | L2 | fuzzed spike, 0 fails |
| `D16CB05` | $16:CB05 | `_00cb05_c` | field | L2 | fuzzed spike, 0 fails |
| `D16CB72` | $16:CB72 | `_00cb72_c` | field | L2 | fuzzed spike, 0 fails |
| `D16CFC4` | $16:CFC4 | `Special_1d_c` | field | L2 | fuzzed spike, 0 fails |
| `D16CFD0` | $16:CFD0 | `Special_1c_c` | field | L2 | fuzzed spike, 0 fails |
| `D16D263` | $16:D263 | `LoadOverworldLeviathan_c` | field | L2 | fuzzed spike, 0 fails |
| `D16D342` | $16:D342 | `Special_0d_c` | field | L2 | fuzzed spike, 0 fails |
| `D16D36D` | $16:D36D | `LoadMapStack_c` | field | L2 | fuzzed spike, 0 fails |
| `D16D758` | $16:D758 | `DrawDestroyedDamcyan_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D16D831` | $16:D831 | `Special_1e_c` | field | L2 | fuzzed spike, 0 fails |
| `D16D9D6` | $16:D9D6 | `Special_06_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D16DB71` | $16:DB71 | `DrawRedWings_c` | field | DELEG | delegate wrapper — equivalent by construction (executes the asm) |
| `D16DBBE` | $16:DBBE | `IncBrightness_c` | field | L2 | fuzzed spike, 0 fails |
| `D16DBD2` | $16:DBD2 | `LoadOverworldIntro_c` | field | L2 | fuzzed spike, 0 fails |
| `D16DE1B` | $16:DE1B | `_00de1b_c` | field | L2 | fuzzed spike, 0 fails |
| `D16DF53` | $16:DF53 | `_00df53_c` | field | L2 | fuzzed spike, 0 fails |
| `D16F533` | $16:F533 | `UpdateBG2Scroll_c` | field | L2 | fuzzed spike, 0 fails |
| `D16F922` | $16:F922 | `_00f922_c` | field | L2 | fuzzed spike, 0 fails |
| `D16FB93` | $16:FB93 | `TfrBG2Tilemap_c` | field | L2 | fuzzed spike, 0 fails |
| `D16FFAB` | $16:FFAB | `DecodeBG1Tilemap_c` | field | L2 | fuzzed spike, 0 fails |
| `D1E9F6C` | $1E:9F6C | `UpdateLocalTiles_c` | field | L2 | hardcore PASS |
| `D1EA03E` | $1E:A03E | `BoardChoco_c` | field | L2 | fuzzed spike, 0 fails |
<!-- REGISTRY:TABLE1:END -->

> **Routines deliberately kept in the interpreter** (removed from the dispatch,
> not regressions): `ExecCmd` ($03:B0FF), `TimerDur_0b/03/07`, `Cmd_0f/0e/0c/08/01`.
> See [REPRISE.md](REPRISE.md).

---

## Table 2 — In-game behavioral validation

Populated by **WF-VALID** ([workflows/WF-VALID.md](workflows/WF-VALID.md)) — → L3.

| ID | Savestate | Frames | WRAM CRC (native) | WRAM CRC (interp) | Drift | Final PC | Maturity | Date |
|----|-----------|--------|-------------------|-------------------|-------|----------|----------|------|
| _(empty — to be populated by WF-VALID)_ | | | | | | | | |

---

## Table 3 — G&W Releases

Populated by **WF-RELEASE** ([workflows/WF-RELEASE.md](workflows/WF-RELEASE.md)).

| Date | Commit | Embedded dispatches | Speed | Fidelity | Crash-free | Notes |
|------|--------|---------------------|-------|----------|------------|-------|
| _(empty — to be populated by WF-RELEASE)_ | | | | | | |
