# BACKLOG — Réalignement existant → cible

> Chantiers pour amener les deux projets à l'organisation décrite dans
> [AGENTS.md](AGENTS.md). Cases à cocher, avec responsable (🤖 agent / 🧑 humain)
> et dépendances. Distinct de [REPRISE.md](REPRISE.md) (requalification des
> routines) — ici, l'**infrastructure** de la démarche.

---

## 1. Répertoire chapeau & sous-modules

- [x] 🤖 Créer `ff4/` avec `CLAUDE.md` (`@AGENTS.md`) et `AGENTS.md`
- [x] 🤖 Rédiger les documents de suivi (`DISPATCH_REGISTRY`, `BACKLOG`, `REPRISE`)
- [x] 🤖 Rédiger les workflows (`WF-DECOMP`, `WF-VALID`, `WF-RELEASE`)
- [x] 🤖 Pousser les commits locaux `ff4-gnw` (→ `origin/main` bf685b5)
- [x] 🤖 Pousser les commits locaux `ff4-port` (→ `origin/main` da2e5dc)
- [x] 🤖 Initialiser `ff4/` comme repo git + créer `hcross/ff4` (public) sur GitHub
- [x] 🤖 Déplacer les working trees sous `ff4/` et les monter en sous-modules
- [x] 🤖 Chemins relatifs préservés (`FF4GNW ?= ../../ff4-gnw` → `ff4/ff4-gnw` ✓,
      savestates `../*.lss` déplacés avec `ff4-port` ✓)

## 2. Registre des dispatches

- [x] 🤖 Peupler la Table 1 depuis `dispatch_all.c` (206 entrées, niveau initial L1/L0)
- [x] 🤖 Auditer chaque dispatch (2026-06-27) — niveaux fondés sur preuves :
      L0=1 · L1=190 · L2=7 · L3=5 · EXCL=3. Sources : hardcore_log PASS,
      KNOWN_FINDINGS (wram_diff=0), fixes F10/F12, DMA-bypass exclus.
- [x] 🤖 Promotion L1→L2 en masse (2026-06-27) : `translator/batch_spike_ffgnw.py`
      sur les corps `ff4-gnw` — **134 PASS** crédités L2 (spike fuzzé 200 essais).
- [ ] 🤖 Traiter les 2 `fail` (vraies divergences) : `CheckMenu_c` (1/200),
      `TfrBGAnimGfx_c` (2/200) — via WF-VALID
- [x] 🤖 Décomposer + résorber les 35 « build_error » (2026-06-28) : 12 delegate
      → DELEG ; 19 run_hang (faux hangs = budget compound, relancés trials réduits
      / run-timeout long → **L2**) ; 2 parser_error UpdateBG2Scroll (parser durci
      → **L2**) ; restent 2 compile_error.
- [ ] 🤖 Traiter les 2 `fail` (vraies divergences) : `CheckMenu_c` (1/200),
      `TfrBGAnimGfx_c` (2/200, DMA) — via WF-VALID
- [ ] 🤖 2 `compile_error` : `RandXA_c` (dépend de `Div16_c` non inclus + appel
      3-args) ; `TfrVRAM_c` (`#include dispatch_all.h` absent du build spike)
- [ ] 🤖 Ajouter un CONTRACT aux 8 `no_contract` ; spikes custom pour les 11
      `no_source` (btlgfx bundlés dans `battle/btlgfx_prim.c`/`btlgfx_monsters.c`)
- [ ] 🤖 Renseigner la Table 2 (validation oracle) au fil de WF-VALID
- [ ] 🤖 Renseigner la Table 3 (releases) au fil de WF-RELEASE

## 3. Équivalence runtime & tests *(infra largement EXISTANTE)*

- [x] 🤖 ~~Recompilation ASM c65 bit-à-bit~~ — **abandonnée** (cc65 cible le 6502,
      inatteignable ; preuve = équivalence runtime, cf. ADR oracle/WF-DECOMP)
- [x] 🤖 Harnais d'équivalence **runtime par routine** : `parity/` +
      `translator/generate_spike.py` (spike C vs asm-interprétée) — EXISTE
- [x] 🤖 Équivalence **ROM/frame** : `ff4-parity-compare` + `oracle_ab` — EXISTE
- [ ] 🤖 **WF-DECOMP §5** — étendre le harnais spike pour injecter des **états
      d'entrée synthétiques** (cas aux limites : 0, max, carry, débordements,
      indices extrêmes) que les savestates ne traversent pas
- [ ] 🤖 Brancher `generate_spike.py` sur l'arbre `port/` courant et re-valider
      en masse (créditer les L2 dans le registre — cf. §5 Reprise)
- [ ] 🤖 Automatiser l'oracle de release (GDB batch) pour minimiser l'humain (WF-RELEASE §5)

## 4. Documentation MemPalace

- [x] 🤖 ADR des 5 décisions de réorganisation (`wing=ff4-gnw, room=architecture-decisions`)
- [ ] 🤖 Vérifier que `wing=snesdev` est peuplé (référence `snes-re`)
- [ ] 🤖 Migrer les findings durables de `KNOWN_FINDINGS.md` vers MemPalace si pertinent

## 5. Reprise des routines

Voir [REPRISE.md](REPRISE.md) — chantier dédié, suivi séparément.

- [x] 🤖 Audit de classification L0→L4 des 206 dispatches (état réel) — voir
      [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md) Table 1
- [ ] 🤖 Liste ordonnée de requalification (priorité chemin critique combat)

## 6. Dette technique connue (depuis KNOWN_FINDINGS + dispatch_all.c)

- [ ] 🤖 `do_*_emu` no-op (`do_fight_cmd_emu`, `do_magic_attack_emu`,
      `do_multi_attack_emu`) → portage réel pour réactiver `Cmd_0f/0e/0c/08/01`
- [ ] 🤖 `RandAITarget_emu`, `SkipAITurn_emu` no-op → IA monstre passive en dispatch
      (bug observé : monstres ne contre-attaquent pas, cf. `[TASK] ff4-combat-visual-bugs`)
- [ ] 🤖 `TimerDur_0b/03` — accès ROM bank $0F (`snes_readByte` au lieu de `ram[]`)
- [ ] 🤖 `TimerDur_07` — wrapper dispatch pour signature non standard `(Snes*, uint16_t x)`
- [ ] 🤖 `ExecSound_ext_stub` — responder SPC réel (réactive musique/SFX)
- [ ] 🤖 `gen_dispatch.py` — déplacer les éditions manuelles de la table dedans
      (TODO inline dans `dispatch_all.c`)

### Dette device du bug-hunt desktop (2026-06-29)

Bugs corrects sur desktop ; restent à rendre **device-correct** (cf. MemPalace
`obstacles-and-solutions`) :

- [x] 🤖 **Bug 3 mode-7** — `InitMapRAM` MMIO : VRAI FIX device (1a86d23)
- [ ] 🤖 **Bug 4 tiles** — `TfrBGGfx` : port `snes_write` fidèle (e02a9e4) mais
      DMA-from-C ne flush pas (classe F6) → interprété sur desktop. Port
      device-correct = **boucle VRAM manuelle** (modèle `TfrSprites_c`/F6) ;
      lit la source DMA pré-réglée (`$4302-4`), écrit en `$2118/$2119`.
- [ ] 🤖 **Bugs 1+2 combat/menu** — requalifier le **batch btlgfx** (14 routines
      no_source, eee0a51) : bug **dynamique** (flicker/animation), plusieurs
      routines fautives en chaîne (bisection oracle frame 0→1→3). Bisection par
      dump statique impossible ; passer par l'oracle per-frame ou A/B SDL
      par routine. Contourné desktop par `host_exclude_divergent`.
- [x] 🤖 **Re-audit MMIO (2026-06-29)** — classe systémique : portage LLM a
      halluciné `sta $21xx/$42xx` en `ram[0x..]` (WRAM) au lieu du bus. Scan
      `ram[0x21xx/0x42xx/0x43xx]` + tri par DB d'entrée.
- [x] 🤖 Corrigées (DB=$00, non-DMA, snes_write, vérifiées sans régression) :
      IncBrightness, AfterCutscene, LoadOverworldIntro, ExecBattle, InitWorld
      (+ InitMapRAM antérieur). Commit ff4-gnw 1741b71.
- [ ] 🤖 **Reste classe DMA** (boucle VRAM manuelle façon F6, device debt) :
      `CloseYesNoWindow`, `TfrPal`, `InitDMA`, `TfrBGAnimGfx`, `TfrLavaGfx`,
      `TfrInvertPal` (+ `TfrBGGfx`). DMA-from-C ne flush pas sur desktop.
- [ ] 🤖 **Vérifier les DB=$7E / DB=ROM** : `_13ddd6/_13eb60/_13ebb8/ExecInterrupt/
      InitCharRows/PlayGameSfx/PlaySystemSfx` (DB=$7E → `$7E:21xx` = WRAM, a priori
      OK) et `LoadTheEndGfx/_13e058` (DB à confirmer). Confirmer cas par cas.

---

**Légende** : 🤖 réalisable par agent · 🧑 nécessite l'humain (hardware, push,
décision). `[x]` = fait · `[ ]` = à faire.
