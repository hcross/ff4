# Registre des dispatches FF4 → G&W

> Registre **vivant** des routines portées et dispatchées. Source de vérité sur
> l'identité, le rôle et la maturité de chaque dispatch. Convention d'ID et
> échelle de maturité définies dans [AGENTS.md](AGENTS.md) §B.1 / §B.2.

**Convention d'ID** : `D<bank><addr>` (6 hex majuscules de la PC SNES).
**Échelle** : `L0` stub · `L1` portée non testée · `L2` tests unitaires C+ASM ·
`L3` validation oracle (`wram_diff=0`) · `L4` testée device.

État initial (généré depuis `ff4-gnw/dispatch_all.c`, 206 entrées) : tout est à
**L1** par défaut sauf les stubs explicites (`L0`). Les annotations renvoient aux
findings de `ff4-port/desktop/KNOWN_FINDINGS.md`. La montée en L2/L3/L4 se fait
via les workflows et se consigne ici.

---

## Table 1 — Décompilation & tests

Maturité statique de chaque routine (existence du code C, état des tests).

| ID | Adresse SNES | Routine C | Domaine | Niveau | Notes / findings |
|----|--------------|-----------|---------|--------|------------------|
| `D00808E` | $00:808E | `AfterBattle_c` | field | L1 |  |
| `D0080A0` | $00:80A0 | `FieldMain_c` | field | L1 |  |
| `D0081F4` | $00:81F4 | `CheckMenu_c` | field | L1 |  |
| `D008302` | $00:8302 | `UpdatePlayerSpeed_c` | field | L1 |  |
| `D00834E` | $00:834E | `InitMapRAM_c` | field | L1 |  |
| `D00883D` | $00:883D | `_00883d_c` | field | L1 |  |
| `D00885E` | $00:885E | `_00885e_c` | field | L1 |  |
| `D00AA58` | $00:AA58 | `CheckTilePass_c` | field | L1 |  |
| `D00AAD8` | $00:AAD8 | `SetPlayerNPCMap_c` | field | L1 |  |
| `D00AB13` | $00:AB13 | `ClearPlayerNPCMap_c` | field | L1 |  |
| `D00AC7D` | $00:AC7D | `CheckVehicleBlock_c` | field | L1 |  |
| `D00BE47` | $00:BE47 | `CalcVehicleSpritePos_c` | field | L1 |  |
| `D00C0C4` | $00:C0C4 | `PlayerSpriteTiles_c` | field | L1 |  |
| `D00C3BD` | $00:C3BD | `UpdateWhalePal_c` | field | L1 |  |
| `D00CB5F` | $00:CB5F | `TfrBGAnimGfx_c` | field | L1 |  |
| `D00F533` | $00:F533 | `UpdateBG2Scroll_c` | field | L1 |  |
| `D00F535` | $00:F535 | `UpdateBG2ScrollSkip_c` | field | L1 |  |
| `D00FFBC` | $00:FFBC | `InitCharProp_ext_c` | field | L1 |  |
| `D00FFE0` | $00:FFE0 | `Vectors_c` | field | L1 |  |
| `D018010` | $01:8010 | `UpdateCtrlField_ext_c` | menu | L1 |  |
| `D01CA85` | $01:CA85 | `TfrVRAM_c` | field | L1 |  |
| `D01D718` | $01:D718 | `FadeIn_c` | field | L1 |  |
| `D01DFD2` | $01:DFD2 | `LoadBattleSpeedPosText_c` | menu | L1 |  |
| `D028560` | $02:8560 | `Mult8_btlgfx_c` | btlgfx | L1 | Mult8 — carry chain complète + sauvegarde cpu->c (NMI) |
| `D0285D2` | $02:85D2 | `HardMult_btlgfx_c` | btlgfx | L1 |  |
| `D0290A0` | $02:90A0 | `TfrBG2MenuTile_c` | btlgfx | L1 |  |
| `D02A491` | $02:A491 | `IncrTextPtr_c` | btlgfx | L1 |  |
| `D02BB0B` | $02:BB0B | `BackAttackYOffset_s_c` | btlgfx | L1 |  |
| `D02BB1A` | $02:BB1A | `BackAttackYOffset_l_c` | btlgfx | L1 |  |
| `D02DA73` | $02:DA73 | `DrawMonsterSprite_c` | btlgfx | L1 |  |
| `D02DAFE` | $02:DAFE | `InitMonsterAnim_c` | btlgfx | L1 |  |
| `D02DCED` | $02:DCED | `BuildOAMEntries_c` | btlgfx | L1 |  |
| `D02DDA5` | $02:DDA5 | `CheckSpriteVisible_c` | btlgfx | L1 |  |
| `D02DDDC` | $02:DDDC | `UpdateMonsterAnim_c` | btlgfx | L1 |  |
| `D038009` | $03:8009 | `ExecBattle_c` | battle | L1 |  |
| `D03805F` | $03:805F | `DrawMP_c` | battle | L1 |  |
| `D038085` | $03:8085 | `ExecBtlGfx_c` | battle | L1 | F10 — ExecBtlGfx_ext via run_emulated_func ; mf non forcé |
| `D0382CB` | $03:82CB | `InitHWRegs_c` | field | L1 |  |
| `D038379` | $03:8379 | `RandXA_c` | battle | L1 |  |
| `D0383B9` | $03:83B9 | `Mult16_c` | battle | L1 |  |
| `D0383E0` | $03:83E0 | `Mult8_c` | battle | L1 |  |
| `D038407` | $03:8407 | `Div16_c` | battle | L1 |  |
| `D0384E3` | $03:84E3 | `Add16_c` | battle | L1 |  |
| `D0384FC` | $03:84FC | `Sub16_c` | battle | L1 |  |
| `D038579` | $03:8579 | `RandMonster_c` | battle | L1 |  |
| `D03858B` | $03:858B | `Rand99_c` | battle | L1 |  |
| `D03859B` | $03:859B | `AddMsg1_c` | battle | L1 |  |
| `D0385A6` | $03:85A6 | `AddMsg2_c` | battle | L1 |  |
| `D0385B1` | $03:85B1 | `AddMsg3_c` | battle | L1 |  |
| `D0387D8` | $03:87D8 | `CheckFanfare_c` | battle | L1 |  |
| `D0387E4` | $03:87E4 | `CheckBattleList_c` | battle | L1 |  |
| `D038803` | $03:8803 | `CheckWinAnim_c` | battle | L1 |  |
| `D0395CE` | $03:95CE | `InitCharRows_c` | battle | L1 |  |
| `D039741` | $03:9741 | `GetPendingAction_c` | battle | L1 | GetPendingAction — chemin ATB (arc F11/F12) |
| `D039788` | $03:9788 | `CheckTimer_c` | battle | L1 | cpu->a sync avant select_obj_emu (arc F12) |
| `D0397B3` | $03:97B3 | `InitAction_c` | battle | L1 | F12 — cpu->a sync avant get_timer_ptr_emu |
| `D039E65` | $03:9E65 | `TimerDur_00_c` | battle | L1 | TimerDur — durée ATB (F11) |
| `D039E71` | $03:9E71 | `TimerDur_02_c` | battle | L1 | TimerDur — durée ATB (F11) |
| `D039F1C` | $03:9F1C | `TimerDur_08_c` | battle | L1 | TimerDur — durée ATB (F11) |
| `D039F75` | $03:9F75 | `TimerDur_0a_c` | battle | L1 | TimerDur — durée ATB (F11) |
| `D039FD8` | $03:9FD8 | `ApplySpeedMod_c` | battle | L1 | ApplySpeedMod — modulateur vitesse ATB (F11) |
| `D03B33F` | $03:B33F | `Cmd_21_c` | battle | L1 |  |
| `D03BA04` | $03:BA04 | `AITarget_1e_c` | battle | L1 |  |
| `D03BA67` | $03:BA67 | `AITarget_1f_c` | battle | L1 |  |
| `D03BA74` | $03:BA74 | `AITarget_20_c` | battle | L1 |  |
| `D03BA81` | $03:BA81 | `AITarget_21_c` | battle | L1 |  |
| `D03BA8E` | $03:BA8E | `AITarget_22_c` | battle | L1 |  |
| `D03BAEF` | $03:BAEF | `AITarget_23_c` | battle | L1 |  |
| `D03BAFE` | $03:BAFE | `AITarget_24_c` | battle | L1 |  |
| `D03BB0D` | $03:BB0D | `AITarget_25_c` | battle | L1 |  |
| `D03BB6B` | $03:BB6B | `AITarget_29_c` | battle | L1 |  |
| `D03BDA9` | $03:BDA9 | `AICond_02_c` | battle | L1 |  |
| `D03BE1E` | $03:BE1E | `AICond_05_c` | battle | L1 |  |
| `D03BE31` | $03:BE31 | `AICond_06_c` | battle | L1 |  |
| `D03BEE4` | $03:BEE4 | `AICond_09_c` | battle | L1 |  |
| `D03BF05` | $03:BF05 | `AICond_0b_c` | battle | L1 |  |
| `D03BFF6` | $03:BFF6 | `AICondTarget_25_c` | battle | L1 |  |
| `D03C03B` | $03:C03B | `AICondTarget_26_c` | battle | L1 |  |
| `D03C042` | $03:C042 | `AICondTarget_27_c` | battle | L1 |  |
| `D03C049` | $03:C049 | `AnyTarget_c` | battle | L1 |  |
| `D03C06C` | $03:C06C | `AICondTarget_23_c` | battle | L1 |  |
| `D03C987` | $03:C987 | `CalcHits_c` | battle | L1 |  |
| `D03D378` | $03:D378 | `MagicDmgEffect_c` | battle | L1 |  |
| `D03D466` | $03:D466 | `MagicEffect_04_c` | battle | L1 |  |
| `D03D613` | $03:D613 | `MagicEffect_08_c` | battle | L1 |  |
| `D03D83F` | $03:D83F | `MagicEffect_0d_c` | battle | L1 |  |
| `D03D863` | $03:D863 | `MagicEffect_0e_c` | battle | L1 |  |
| `D03D972` | $03:D972 | `MagicEffect_13_c` | battle | L1 |  |
| `D03D9EC` | $03:D9EC | `MagicEffect_15_c` | battle | L1 |  |
| `D03DA0C` | $03:DA0C | `MagicEffect_16_c` | battle | L1 |  |
| `D03DC9B` | $03:DC9B | `MagicEffect_20_c` | battle | L1 |  |
| `D03DCBB` | $03:DCBB | `MagicEffect_21_c` | battle | L1 |  |
| `D03DCD6` | $03:DCD6 | `MagicEffect_22_c` | battle | L1 |  |
| `D03DD06` | $03:DD06 | `MagicEffect_24_c` | battle | L1 |  |
| `D03DD65` | $03:DD65 | `MagicEffect_2c_c` | battle | L1 |  |
| `D03DD95` | $03:DD95 | `MagicEffect_28_c` | battle | L1 |  |
| `D03DDB1` | $03:DDB1 | `MagicEffect_2a_c` | battle | L1 |  |
| `D03DDC9` | $03:DDC9 | `MagicEffect_2b_c` | battle | L1 |  |
| `D03DDDD` | $03:DDDD | `MagicEffect_2f_c` | battle | L1 |  |
| `D03DFD2` | $03:DFD2 | `MagicEffect_32_c` | battle | L1 |  |
| `D03E030` | $03:E030 | `RemoveTarget_c` | battle | L1 |  |
| `D03E100` | $03:E100 | `CheckStrongElem_c` | battle | L1 |  |
| `D03E133` | $03:E133 | `CheckWeakElem_c` | battle | L1 |  |
| `D03E43B` | $03:E43B | `Cmd_22_c` | battle | L1 |  |
| `D03E4D9` | $03:E4D9 | `TwinFailed_c` | battle | L1 |  |
| `D03FE03` | $03:FE03 | `TfrSprites_c` | field | L1 | F6 — réimplémenté OAM manuel ; exclu baseline (DMA-bypass) |
| `D048004` | $04:8004 | `ExecSound_ext_stub` | sound: | L0 | F4 — stub no-op (débloque le titre ; SPC non implémenté) |
| `D0485E1` | $04:85E1 | `PlayGameSfx_c` | sound | L1 |  |
| `D04861E` | $04:861E | `ExecInterrupt_c` | sound | L1 |  |
| `D088690` | $08:8690 | `LoadTitleGfx_c` | field | L1 |  |
| `D08885E` | $08:885E | `TfrTitleCrystalTiles_c` | field | L1 |  |
| `D0E8B3C` | $0E:8B3C | `CheckBattle_c` | field | L1 |  |
| `D12E35B` | $12:E35B | `WaitVblankEvent_c` | field | L1 |  |
| `D12E55A` | $12:E55A | `FindEventTerminator_c` | field | L1 |  |
| `D12E613` | $12:E613 | `EventCmd_d8_c` | field | L1 |  |
| `D12E7D3` | $12:E7D3 | `EventCmd_d7_c` | field | L1 |  |
| `D12EB47` | $12:EB47 | `EventCmd_e0_c` | field | L1 |  |
| `D12EC06` | $12:EC06 | `EventCmd_e6_c` | field | L1 |  |
| `D12EC3E` | $12:EC3E | `EventCmd_dd_c` | field | L1 |  |
| `D12ED1D` | $12:ED1D | `SetCurrGil_c` | field | L1 |  |
| `D12EE1C` | $12:EE1C | `EventCmd_d0_c` | field | L1 |  |
| `D12EE25` | $12:EE25 | `EventCmd_d1_c` | field | L1 |  |
| `D12EE35` | $12:EE35 | `TfrInvertPal_c` | field | L1 |  |
| `D13BFE3` | $13:BFE3 | `_00bfe3_c` | field | L1 |  |
| `D13C11F` | $13:C11F | `ReloadNPCs_c` | field | L1 |  |
| `D13D730` | $13:D730 | `LoadTheEndGfx_c` | cutscene | L1 |  |
| `D13DB10` | $13:DB10 | `_13db10_c` | cutscene | L1 |  |
| `D13DB23` | $13:DB23 | `_13db23_c` | cutscene | L1 |  |
| `D13E07D` | $13:E07D | `_13e07d_c` | cutscene | L1 |  |
| `D13E139` | $13:E139 | `GetEarthSpritePos_c` | cutscene | L1 |  |
| `D13E247` | $13:E247 | `InitStars_c` | cutscene | L1 |  |
| `D13E2DC` | $13:E2DC | `GetOtherPlanetTile_c` | cutscene | L1 |  |
| `D13E512` | $13:E512 | `Mult16_1_c` | cutscene | L1 |  |
| `D13EB24` | $13:EB24 | `NewLine_c` | cutscene | L1 |  |
| `D13EB60` | $13:EB60 | `_13eb60_c` | cutscene | L1 |  |
| `D13EBB8` | $13:EBB8 | `_13ebb8_c` | cutscene | L1 |  |
| `D13EF4C` | $13:EF4C | `_13ef4c_c` | cutscene | L1 |  |
| `D13FE36` | $13:FE36 | `AutoBattle_0003_c` | battle | L1 |  |
| `D14F58E` | $14:F58E | `_14f58e_c` | field | L1 |  |
| `D14F626` | $14:F626 | `GilWindowTiles3_c` | field | L1 |  |
| `D14F63E` | $14:F63E | `GilWindowTiles4_c` | field | L1 |  |
| `D14F6D6` | $14:F6D6 | `DlgTilesTop_c` | field | L1 |  |
| `D14F796` | $14:F796 | `MapTitleTilesTop_c` | field | L1 |  |
| `D14F7B6` | $14:F7B6 | `MapTitleTilesBtm_c` | field | L1 |  |
| `D14FA16` | $14:FA16 | `LavaAnimPal_c` | field | L1 |  |
| `D14FB1E` | $14:FB1E | `WipeScanlineTbl_c` | field | L1 |  |
| `D14FD00` | $14:FD00 | `InitCtrl_ext2_c` | menu | L1 |  |
| `D14FD03` | $14:FD03 | `UpdateCtrl_ext_c` | menu | L1 |  |
| `D14FD06` | $14:FD06 | `ClearText_ext_c` | menu | L1 |  |
| `D14FD09` | $14:FD09 | `UpdateWindowColor_ext_c` | menu | L1 |  |
| `D14FD0C` | $14:FD0C | `UpdateScrollRegs_ext_c` | menu | L1 |  |
| `D1585AB` | $15:85AB | `InitWorld_c` | field | L1 |  |
| `D1589ED` | $15:89ED | `InitInterrupts_c` | field | L1 |  |
| `D158B2A` | $15:8B2A | `InitDMA_c` | field | L1 |  |
| `D158D5D` | $15:8D5D | `PlayMapSong_c` | field | L1 |  |
| `D158DFC` | $15:8DFC | `WaitKeyUp_c` | field | L1 |  |
| `D158E05` | $15:8E05 | `WaitKeyDown_c` | field | L1 |  |
| `D158E47` | $15:8E47 | `UpdateWaterLavaAnim_c` | field | L1 |  |
| `D158E57` | $15:8E57 | `TfrWaterLavaGfx_c` | field | L1 |  |
| `D158F34` | $15:8F34 | `TfrLavaGfx_c` | field | L1 |  |
| `D159104` | $15:9104 | `UpdateMode7Regs_c` | field | L1 |  |
| `D1591CA` | $15:91CA | `UpdateWipeIRQ_c` | field | L1 |  |
| `D159204` | $15:9204 | `UpdateWipeNMI_c` | field | L1 |  |
| `D159792` | $15:9792 | `LoadPlayerGfxWorld_c` | field | L1 |  |
| `D1597A2` | $15:97A2 | `LoadPlayerGfxSub_c` | field | L1 |  |
| `D1599FB` | $15:99FB | `GiveGil_c` | field | L1 |  |
| `D159AE9` | $15:9AE9 | `GetTreasureTiles_c` | field | L1 |  |
| `D159B5B` | $15:9B5B | `GetTreasurePtr_c` | field | L1 |  |
| `D15AF24` | $15:AF24 | `CloseYesNoWindow_c` | field | L1 |  |
| `D15B09C` | $15:B09C | `ScrollItemListDown_c` | field | L1 |  |
| `D15B143` | $15:B143 | `TfrBGGfx_c` | field | L1 |  |
| `D15B3DC` | $15:B3DC | `_15b3dc_c` | field | L1 |  |
| `D15B41B` | $15:B41B | `GetDlgPtr1H_c` | field | L1 |  |
| `D15B6F1` | $15:B6F1 | `InitDlgIRQ_c` | field | L1 |  |
| `D15B8C9` | $15:B8C9 | `_15b8c9_c` | field | L1 |  |
| `D15BB6A` | $15:BB6A | `_15bb6a_c` | field | L1 |  |
| `D15C144` | $15:C144 | `_15c144_c` | field | L1 |  |
| `D15C163` | $15:C163 | `_15c163_c` | field | L1 | F7 — branche inversée + DP corrigés ; oracle 0 diff |
| `D15C23D` | $15:C23D | `_15c23d_c` | field | L1 |  |
| `D15C37F` | $15:C37F | `Pow10Hi_c` | field | L1 |  |
| `D15CA5E` | $15:CA5E | `_15ca5e_c` | field | L1 | F11(KF) — palette DMA-bypass incomplet ; exclu baseline |
| `D15CA85` | $15:CA85 | `_15ca85_c` | field | L1 |  |
| `D15CADC` | $15:CADC | `_15cadc_c` | field | L1 | F3 — DMA-bypass OAM ; exclu baseline |
| `D16C59A` | $16:C59A | `AfterCutscene_c` | field | L1 |  |
| `D16C8BC` | $16:C8BC | `Special_2d_c` | field | L1 |  |
| `D16CB05` | $16:CB05 | `_00cb05_c` | field | L1 |  |
| `D16CB72` | $16:CB72 | `_00cb72_c` | field | L1 |  |
| `D16CFC4` | $16:CFC4 | `Special_1d_c` | field | L1 |  |
| `D16CFD0` | $16:CFD0 | `Special_1c_c` | field | L1 |  |
| `D16D263` | $16:D263 | `LoadOverworldLeviathan_c` | field | L1 |  |
| `D16D342` | $16:D342 | `Special_0d_c` | field | L1 |  |
| `D16D36D` | $16:D36D | `LoadMapStack_c` | field | L1 |  |
| `D16D758` | $16:D758 | `DrawDestroyedDamcyan_c` | field | L1 |  |
| `D16D831` | $16:D831 | `Special_1e_c` | field | L1 |  |
| `D16D9D6` | $16:D9D6 | `Special_06_c` | field | L1 |  |
| `D16DB71` | $16:DB71 | `DrawRedWings_c` | field | L1 |  |
| `D16DBBE` | $16:DBBE | `IncBrightness_c` | field | L1 |  |
| `D16DBD2` | $16:DBD2 | `LoadOverworldIntro_c` | field | L1 |  |
| `D16DE1B` | $16:DE1B | `_00de1b_c` | field | L1 |  |
| `D16DF53` | $16:DF53 | `_00df53_c` | field | L1 |  |
| `D16F533` | $16:F533 | `UpdateBG2Scroll_c` | field | L1 |  |
| `D16F922` | $16:F922 | `_00f922_c` | field | L1 |  |
| `D16FB93` | $16:FB93 | `TfrBG2Tilemap_c` | field | L1 |  |
| `D16FFAB` | $16:FFAB | `DecodeBG1Tilemap_c` | field | L1 |  |
| `D1E9F6C` | $1E:9F6C | `UpdateLocalTiles_c` | field | L1 |  |
| `D1EA03E` | $1E:A03E | `BoardChoco_c` | field | L1 |  |

> **Routines volontairement en interpréteur** (retirées du dispatch, pas des
> régressions) : `ExecCmd` ($03:B0FF, tail-jump `jml [$0080]`),
> `TimerDur_0b/03/07` ($03:9E85/9E99/9F03, accès ROM bank $0F non porté ou
> signature non standard), `Cmd_0f/0e/0c/08/01` (helpers `do_*_emu` no-op →
> dégâts avalés). Voir [REPRISE.md](REPRISE.md) pour leur requalification.

---

## Table 2 — Validation comportementale en jeu

Renseignée par **WF-VALID** (voir [workflows/WF-VALID.md](workflows/WF-VALID.md)).
Une ligne par dispatch ayant passé une validation oracle isolée.

| ID | Savestate | Frames | CRC WRAM (natif) | CRC WRAM (interp) | Dérive | PC final | Maturité | Date |
|----|-----------|--------|------------------|-------------------|--------|----------|----------|------|
| _(vide — à peupler par WF-VALID)_ | | | | | | | | |

**Légende dérive** : `0` = identique byte-à-byte (hors masque stack) ; `Nb` =
N octets divergents (détailler la zone) ; `artefact` = divergence due au
déphasage cycles (cf. AGENTS §A.2), non significative.

---

## Table 3 — Releases G&W

Renseignée par **WF-RELEASE** (voir [workflows/WF-RELEASE.md](workflows/WF-RELEASE.md)).
Une ligne par build flashé et testé sur device.

| Date | Commit | Dispatches embarqués | Vitesse | Fidélité | Crash-free | Notes |
|------|--------|----------------------|---------|----------|------------|-------|
| _(vide — à peupler par WF-RELEASE)_ | | | | | | |

**Axes de qualité** :
- **Vitesse** : taux de dispatch (%), frames/s effectives, temps WaitVblank.
- **Fidélité** : screenshots pixel-diff vs référence sur scènes clés.
- **Crash-free** : oracle de liveness (frames qui avancent), SCB/CFSR à 0, pas
  de runaway/spin sur N minutes.
