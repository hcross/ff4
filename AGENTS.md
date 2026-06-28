# FF4 → Game & Watch — Contexte de la démarche

> Point de lancement de l'outil CLI pour le portage de **Final Fantasy IV**
> (Super Famicom, NTSC-J) sur **Nintendo Game & Watch** (STM32H7B0).
> Ce fichier porte le contexte **stable** valable pour les deux sous-projets,
> survit aux compactions, et pointe vers les documents de suivi **vivants**.

---

## A — Contexte statique

### A.1 Les deux projets

La démarche est répartie sur deux dépôts, montés comme **sous-modules git** de
ce répertoire chapeau (`ff4/`).

| Projet | Rôle | Contenu clé |
|--------|------|-------------|
| **`ff4-gnw/`** | Sources C du port — l'artefact qui tourne sur le device | Table de dispatch (`dispatch_all.c`/`.h`), routines portées (`battle/`, `field/`, `menu/`, `cutscene/`, `sound/`), helpers LakeSnes (`ff4_helpers.c`), fork LakeSnes (`snes/`), glue G&W (`main.c`) |
| **`ff4-port/`** | Infrastructure de validation — l'oracle et la vérité terrain | Désassemblage de référence (`upstream/notes/ff4j-sfc.asm`), ROM (`upstream/rom/ff4-jp1.sfc`), harness desktop (`desktop/`), savestates de référence (`*.lss`), `desktop/KNOWN_FINDINGS.md` |

`ff4-gnw` se compile **deux fois** depuis les mêmes sources C :
- pour le **device** (STM32H7B0, via le build retro-go-sd) ;
- pour le **desktop headless** (validation), via `ff4-port/desktop/Makefile` qui
  lie l'arbre `ff4-gnw` vivant (`FF4GNW ?= ../../ff4-gnw`).

### A.2 Intention générale

Porter FF4 sur Game & Watch en **remplaçant progressivement** les routines SNES
interprétées par du C natif *dispatché*. LakeSnes (interpréteur 65816) sert à la
fois de moteur d'exécution embarqué et de **référence de vérité** : chaque
routine portée doit être prouvée équivalente à l'originale avant d'être trustée.

Le mécanisme central est le **dispatch** : `ff4_dispatch_try()` (dans
`dispatch_all.c`) intercepte les `JSR`/`JSL` (opcodes `0x20`/`0x22`) vers une
adresse SNES connue et exécute la routine C correspondante au lieu de
l'interpréter. Le `JML` (`0xDC`) **n'est pas intercepté** — d'où certaines
routines à fin tail-jump qui doivent rester en interpréteur.

> ⚠ **Limites connues du dispatch** (à garder en tête en permanence) :
> - Le write-hook WRAM (`snes_wram_write_hook`) est **aveugle aux écritures C
>   directes** (`snes->ram[x] = v`). Tracer une routine dispatchée passe par
>   `--trace-frame` ou un `printf` embarqué, pas par un watchpoint WRAM.
> - L'interpréteur pur est **~6× plus lent en frames headless** sur le chemin
>   `WaitVblank` : la garde anti-hang de `snes_runFrameBounded` (50M opcodes/
>   frame) force la sortie. **Comparer à `frames_run` SNES égal**, jamais à
>   nombre de frames headless égal.
> - `ff4_dispatch_try` ne charge pas le coût en cycles de la routine originale
>   → léger déphasage temporel PPU entre passe native et passe interprétée.

### A.3 Topologie & prérequis sous-modules

```
ff4/                          ← repo chapeau (point de lancement CLI)
├── CLAUDE.md                 ← @AGENTS.md
├── AGENTS.md                 ← ce fichier (contexte stable)
├── DISPATCH_REGISTRY.md      ← registre vivant des dispatches (IDs, maturité)
├── BACKLOG.md                ← chantiers de réalignement existant → cible
├── REPRISE.md                ← reset sélectif des assets (requalification)
├── workflows/
│   ├── WF-DECOMP.md          ← décompilation + validation formelle d'une routine
│   ├── WF-VALID.md           ← validation comportementale en jeu (oracle + GDB)
│   └── WF-RELEASE.md         ← build + test G&W, table de releases
├── ff4-gnw/   (submodule)
└── ff4-port/  (submodule)
```

**Prérequis avant de figer les sous-modules** : un sous-module git référence un
**commit poussé** sur le remote. Les commits locaux de `ff4-gnw` / `ff4-port`
doivent être poussés (ex. Gitea « Odan ») avant que le chapeau ne les épingle.
Tant que la mise en sous-modules n'est pas faite, ce répertoire héberge
seulement la documentation et les deux projets restent à leur emplacement
courant. Suivi dans [BACKLOG.md](BACKLOG.md).

### A.4 Outils disponibles

#### Plugins Claude Code (marketplace local)

| Plugin / Skill | Usage |
|----------------|-------|
| **`snes-re`** (agent `snes-reverse-engineer`) | Analyse 65816, reverse-engineering, portage asm→C. **Analyse uniquement** — handoff à `gnw-hardware` pour le device. |
| `snes-re:snes-asm` | Référence + modèle mental 65816 ; pièges récurrents inline, référence matérielle lourde dans MemPalace `wing=snesdev`. |
| `snes-re:asm-to-c-port` | **Procédure de portage** side-by-side-compare (méthodo zelda3/smw) : overlay `g_ram` aux adresses d'origine, harness compare par frame, pont `run_emulated_func`, patch ROM pour bugs d'origine, validation par screenshot. |
| `snes-re:disasm-trace` | Outillage de désassemblage : tracing code/data avec suivi des flags m/x, mapping LoROM/HiROM, recoupement avec une réf. |
| **`gnw-hardware:provision`** | Build + flash + recovery device (gnwmanager, openocd, ST-Link SWD). **Hardware-in-the-loop** : connexion sonde / power on / lecture LCD = humain. |
| **`gnw-hardware:debug`** | Diagnostic on-device via `gnwmanager gdbserver` + `arm-none-eabi-gdb` : décodage fault Cortex-M (SCB/CFSR/HFSR), intégrité vector-table, **oracle de liveness frames**, classification runaway/spin/clean-return. |

> **Règles d'or `snes-re`** (causes des bugs historiques FF4) :
> 1. **Le direct-page register (D) est le piège n°1.** Tout opérande `$nn` est
>    `[D + nn]` (bank `$00`), PAS `$00nn`. FF4 field/NMI tournent avec `D=$0600`.
> 2. **Les octets de la ROM sont la vérité**, pas les annotations du désassemblage.
> 3. **Suivre les flags m/x** (REP/SEP) pour dimensionner immédiats et opcodes.
> 4. **Valider chaque incrément de rendu par screenshot** (pixel-diff), jamais
>    par fps/compteur de frames/registre de fault seuls.

#### Harness desktop (`ff4-port/desktop/`)

Lie l'arbre `ff4-gnw` vivant. Compilé sous le **même contrat** que le device
(`-DFF4_PORT_STATIC_SNES` : singleton `Snes` statique, dims `pixelBuffer`
device, hook `ff4_dispatch_try` dans `cpu.c`). `make all` produit :

| Binaire | Rôle | Flags clés |
|---------|------|-----------|
| `ff4-desktop-headless` | Exécution N frames, dump frame | `--frames N`, `--load f.lss`, `--out f.ppm`, `--no-dispatch`, `--watch-wram ADDR [--watch-wram-hi HI]`, `--trace-frame N` |
| `ff4-desktop-sdl` | Fenêtre interactive | `--load`, `--save-prefix`, `--scale`. Touches : flèches=d-pad, x=A z=B a=Y s=X d=L c=R, RShift=Select, Return=Start, Espace=pause, `.`=step, `g`=toggle interpréteur (input+son restent natifs), `5`=save slot, `9`=reload, `0`=screenshot |
| `ff4-desktop-oracle` (`oracle_ab.c`) | Comparaison A/B dispatch vs interpréteur, frame par frame ; passe de calibration + **facturation des cycles** (durcissement) | `--load SEED`, `--frames N`, `--exclude HEX` (répétable), `--no-charge` |
| `wram_diff` | Diff byte-exact WRAM entre deux passes | masque la région stack |
| `proof_cyc` | Analyse cycles + progression PC par frame | |
| `miss_profiler` | Tally des PC en miss → liste des routines chaudes à porter | |

Cibles `make` utiles : `make oracle SEED=…`, `make oracle-baseline SEED=…`
(exclut les routines à DMA-bypass intentionnel : `15cadc 048004 03fe03 15ca5e`).

#### Décompilation & équivalence runtime par routine (`ff4-port/`)

| Composant | Rôle |
|-----------|------|
| `ca65-bridge/` | Pont Python de **lecture** du désassemblage ca65 : `get-asm`, `xrefs-from/to`, `search`, `classify` (translate vs delegate, ADR-003). |
| `translator/` | Traduction **asm → C** assistée LLM (`batch_translate.py`, provider enfichable claude-cli / anthropic-sdk / openai-compat ; `--dry-run`, `--budget-usd`). Sortie : `port/<module>/<func>.c`. |
| `parity/` | Équivalence **runtime**. `generate_spike.py` → `spike__<addr>_*.c` : C porté vs `run_emulated_func` (asm interprétée) à état d'entrée identique → compare l'état de sortie (**preuve L2**). `ff4-parity-compare` : deux ROMs en lock-step, memcmp WRAM/SRAM/VRAM/OAM/CGRAM par frame. |

> `ca65`/`cl65` (suite cc65) sont installés mais servent au sous-module
> `upstream` à réassembler le désassemblage en **ROM vanilla de référence** — pas
> à recompiler le C porté. Il n'y a **pas** de comparaison bit-à-bit C→ASM (voie
> abandonnée, cf. §B.2). `port/` est la zone de traduction ; une routine validée
> par son spike est promue vers `ff4-gnw/<domaine>/`.

#### Particularités LakeSnes (fork dans `ff4-gnw/snes/`)

- `snes_runFrameBounded` — garde anti-hang (50M opcodes/frame). Cause du facteur
  6× interpréteur (cf. A.2).
- `snes_wram_write_hook` — watchpoint WRAM, **aveugle au C** (cf. A.2).
- `run_emulated_func(snes, pc)` — exécute une adresse SNES dans l'interpréteur
  depuis le C (pont incrémental une-routine-à-la-fois).

### A.5 Documentation de référence

- **MemPalace** (mémoire agent persistante cross-outil) :
  - `wing=ff4-gnw` : `room=architecture-decisions` (ADR), `room=obstacles-and-solutions`,
    `room=task-handoff` (lane de reprise `[TASK:*]`).
  - `wing=snesdev` : référence matérielle 65816/PPU/DMA/APU, alimentée par
    `snes-re` (`room=ref-<source>`, `room=pitfalls`). Interrogée par
    `mempalace_search(wing="snesdev", room="ref-…", …)`.
- **`ff4-port/desktop/KNOWN_FINDINGS.md`** : findings F1→F12 documentés avec
  reproduction, cause racine, fix et validation. **Source de vérité** sur l'état
  des bugs connus ; à lire avant de retoucher une routine déjà investiguée.

---

## B — Contexte dynamique

### B.1 Identifiant unique des dispatches

Format : **`D<bank><addr>`** — dérivé mécaniquement de l'adresse SNES (6 chiffres
hexadécimaux majuscules de la PC `bank:addr`).

```
D0397B3  → $03:97B3  InitAction_c
D0383B9  → $03:83B9  Mult16_c
D03FE03  → $03:FE03  TfrSprites_c
```

Propriétés : unique, sans collision, stable tant que la routine ne change pas
d'adresse, calculable sans registre central. Chaque dispatch est référencé par
cet ID dans **tous** les workflows, le registre, les commits et MemPalace.

### B.2 Échelle de maturité L0 → L4

Niveau **cumulatif** : un dispatch ne passe à `Ln+1` qu'après avoir satisfait `Ln`.

| Niveau | Signification | Critère de passage |
|--------|---------------|--------------------|
| **L0** | Stub no-op | Présent dans la table mais corps vide / `_emu` no-op. À traiter ou retirer. |
| **L1** | Portée, non testée | Corps C écrit, compile, mais aucune preuve d'équivalence. |
| **L2** | Équivalence runtime par routine | Le **spike** passe : C vs asm-interprétée à état d'entrée identique → mêmes sorties (`parity/`, `generate_spike.py`). Couverture aux limites à formaliser. |
| **L3** | Validation oracle | Savestate isolé (seul ce dispatch actif), `wram_diff = 0`, pas de dérive. |
| **L4** | Validée device | Intégrée au build G&W, testée sur device (oracle liveness + screenshot), pas de crash. |

> **Pas de recompilation bit-à-bit C→ASM** : voie abandonnée (cc65 cible le
> 6502, jamais d'égalité d'octets avec l'asm 65816 écrit à la main). La preuve
> d'équivalence est *runtime* (spike par routine, puis oracle en jeu), méthode
> zelda3/snesrev. L'infra spike **existe déjà** (`parity/`, `translator/`).
>
> **Audit + promotion spike (2026-06-27/28)** : L0=1 · L1=44 · L2=141 · L3=5 ·
> EXCL=3 · **DELEG=12**. 134 PASS crédités L2 via `batch_spike_ffgnw.py` (spike
> fuzzé 200 essais sur les corps `ff4-gnw`). Le fourre-tout « build_error » a été
> décomposé : 12 delegate wrappers → **DELEG** (équivalents par construction),
> 19 run_hang, 3 parser_error, 1 compile_error. Les 44 L1 restants : 19 run_hang,
> 11 no_source (btlgfx), 8 no_contract, 3 parser_error, 2 fail, 1 compile_error.
> `DELEG` = wrapper exécutant l'asm via `run_emulated_func` (correct mais pas un
> portage natif). Détail + méthodo : [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md).

### B.3 Workflows (résumé)

Le déroulé **détaillé et précis** de chaque workflow est dans `workflows/`.
Chaque workflow utilise **MemPalace** pour le suivi long-terme et
**sequential-thinking** pour les sous-tâches multi-tours.

| Workflow | But | Détail |
|----------|-----|--------|
| **WF-DECOMP** | Décompiler une routine ASM → C (manuel ou LLM), prouver l'**équivalence runtime** par routine via le spike, la consigner (L2) | [workflows/WF-DECOMP.md](workflows/WF-DECOMP.md) |
| **WF-VALID** | Valider le comportement en jeu via l'oracle (savestate isolé, CRC/screenshot, GDB si besoin) | [workflows/WF-VALID.md](workflows/WF-VALID.md) |
| **WF-RELEASE** | Construire et tester la version G&W, mesurer la qualité (vitesse, fidélité, crash-free) | [workflows/WF-RELEASE.md](workflows/WF-RELEASE.md) |

### B.4 Protocole de rétablissement post-compaction

À exécuter **en début de session** et **après toute compaction** avant de
reprendre le travail :

1. **Calculer `<project-name>`** = `ff4-gnw` (wing de référence du portage).
2. **`mempalace_status`** — énumérer les wings ; exclure `transcripts*`.
3. **Lookup handoff** :
   `mempalace_search(query="[TASK:ongoing]", wing="ff4-gnw", room="task-handoff")`.
   Appliquer le filtre `visible_to` côté client.
4. **Lire ce fichier** (`AGENTS.md`) pour le contexte statique.
5. **Lire [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md)** pour l'état des dispatches,
   et [REPRISE.md](REPRISE.md) pour le chantier de requalification en cours.
6. **Si un `[TASK:ongoing]` existe pour `ff4-gnw`** : écrire **immédiatement** un
   `[TASK:checkpoint]` via `mempalace_update_drawer` (timestamp, `writer_agent`,
   `resumed_from`, `progress`) **AVANT** tout travail effectif. Mandatoire.
7. **`sequential-thinking`** : reconstruire le raisonnement en cours depuis le
   drawer, puis reprendre la sous-tâche au point indiqué par `next:`.

En fin de session : mettre à jour le drawer `[TASK:*]`, consigner décisions
(ADR) et obstacles, écrire une entrée de diary.

### B.5 Documents de suivi vivants

- **[DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md)** — registre des 206 dispatches,
  3 tables (décompilation/tests, validation jeu, releases).
- **[BACKLOG.md](BACKLOG.md)** — chantiers existant → cible.
- **[REPRISE.md](REPRISE.md)** — reset sélectif par couche, ordre de requalification.

---

## Démarrage rapide

```sh
# Build du harness desktop (depuis ff4-port/desktop/)
cd ff4-port/desktop && make all

# Lancer un combat de référence en fenêtre
make sdl ROM=../upstream/rom/ff4-jp1.sfc        # puis charger un .lss avec 9

# Comparaison A/B (dispatch vs interpréteur) sur une savestate
make oracle SEED=../006-in-combat.lss FRAMES=600

# Diff WRAM byte-exact à la frame de divergence
./wram_diff ../upstream/rom/ff4-jp1.sfc ../006-in-combat.lss
```
