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
- [ ] 🤖 Auditer chaque dispatch pour confirmer son niveau **réel** (vs L1 par défaut)
- [ ] 🤖 Renseigner la Table 2 (validation oracle) au fil de WF-VALID
- [ ] 🤖 Renseigner la Table 3 (releases) au fil de WF-RELEASE

## 3. Infrastructure de tests formels *(workflows incomplets)*

- [ ] 🤖 **WF-DECOMP §4** — chaîne de recompilation ASM c65 + comparaison bit-à-bit
      (toolchain c65 à choisir/intégrer). *Bloque l'atteinte de L2 par la
      décompilation.*
- [ ] 🤖 **WF-DECOMP §5** — framework de tests unitaires C + ASM c65 aux limites
- [ ] 🤖 Définir le format de cas de test (entrées WRAM/registres, sorties attendues)
- [ ] 🤖 Automatiser l'oracle de release (GDB batch) pour minimiser l'humain (WF-RELEASE §5)

## 4. Documentation MemPalace

- [x] 🤖 ADR des 5 décisions de réorganisation (`wing=ff4-gnw, room=architecture-decisions`)
- [ ] 🤖 Vérifier que `wing=snesdev` est peuplé (référence `snes-re`)
- [ ] 🤖 Migrer les findings durables de `KNOWN_FINDINGS.md` vers MemPalace si pertinent

## 5. Reprise des routines

Voir [REPRISE.md](REPRISE.md) — chantier dédié, suivi séparément.

- [ ] 🤖 Audit de classification L0→L4 des 206 dispatches (état réel)
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

---

**Légende** : 🤖 réalisable par agent · 🧑 nécessite l'humain (hardware, push,
décision). `[x]` = fait · `[ ]` = à faire.
