# WF-RELEASE — Build & test de la version Game & Watch

> Construire l'image G&W, la flasher, et qualifier le livrable sur trois axes
> (vitesse, fidélité, crash-free) en sollicitant l'humain au **minimum**.
> Pousse les dispatches embarqués vers **L4**.

**Skills** : `gnw-hardware:provision` (build/flash/recovery),
`gnw-hardware:debug` (oracle liveness, fault decode, framebuffer dump).
**Hardware-in-the-loop** : connexion sonde, power on/off et lecture LCD = humain.

---

## Entrée

- Un commit `ff4-gnw` (état de la table de dispatch à embarquer).
- Une sonde ST-Link SWD connectée, unité G&W sous tension.

## Sortie

- Une ligne dans [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 3 :
  date, commit, dispatches embarqués, vitesse, fidélité, crash-free.
- Promotion des dispatches testés sans régression à **L4**.

---

## Étapes

### 0. Rétablissement de contexte
Protocole post-compaction (AGENTS §B.4). `[TASK:ongoing] wf-release-<commit>`.

### 1. Santé sonde & device (humain pour le câblage)
```sh
bash scripts/health-check.sh        # (gnw-hardware:provision) sonde USB + gnwmanager info
```
Si « Unable to autodetect probe » : câble data (pas charge-only), enumération
USB, device sous tension. `Filesystem MISSING/CORRUPT` = souvent un red herring
(FS gnwmanager, pas la LittleFS retro-go).

### 2. Provisionner la ROM si nécessaire
La ROM est chargée au runtime depuis FrogFS (`/roms/homebrew/ff4.sfc`).
**`make clean` détruit la ROM gitignorée** → la re-copier depuis une copie
hors `sd_content/` (ex. `ff4-port/upstream/rom/`). Vérifier la **même SHA-1**
que la cible RE, sinon le dispatch C désynchronise.

### 3. Build (flags canoniques)
```sh
make INTFLASH_BANK=2 FF4_AUTOBOOT=1 SD_CARD=0 EXTFLASH_SIZE_MB=4 \
     CHECK_DIRTY_SUBMODULE=0 -j4 all
```
- `INTFLASH_BANK=2` — app à `0x08100000` (bootloader bank 1 à `0x08000000`).
- `SD_CARD=0` — assets en flash interne. **`SD_CARD=1` rend `flash` silencieusement
  no-op.**
- `make clean` obligatoire si changement de `SD_CARD` ou autre flag fondamental
  (mais re-provisionner la ROM ensuite, §2).

### 4. Flash
```sh
make INTFLASH_BANK=2 FF4_AUTOBOOT=1 SD_CARD=0 EXTFLASH_SIZE_MB=4 \
     CHECK_DIRTY_SUBMODULE=0 flash
```
La recette finit par `start 0x08100000` (saut direct à l'app) + `disable-debug`.
Conséquences :
- Le **vrai test de boot = power-cycle** (passe par le bootloader) ; `start`
  seul ne valide l'app qu'en isolation.
- Après `disable-debug`, la sonde peut nécessiter un power-cycle pour répondre.

### 5. Qualifier — axe **crash-free** (oracle liveness, automatisé)
```sh
bash scripts/gdbserver-up.sh
arm-none-eabi-gdb -q -nx -batch -x scripts/frames-oracle.gdb build/gw_retro_go.elf
```
- `frames` qui **avancent** = émulateur vivant.
- `frames == 0` + PC stable = spin ; + PC qui rampe + backtrace corrompu =
  runaway (souvent bootloader clobbered → recovery `provision §4`).
- Décoder SCB : `VECTACTIVE==0` + `CFSR==0` + `HFSR==0` = pas de HardFault.

### 6. Qualifier — axe **fidélité** (screenshots pixel-diff)
Dump framebuffer device (gnw-hardware:debug) sur scènes clés (titre, champ,
combat) et **pixel-diff** vs référence desktop/connue. Un écran noir avec SCB à
0 n'est **pas** un fault → problème de rendu/titre, pas de boot.

### 7. Qualifier — axe **vitesse**
Mesurer : taux de dispatch (%), frames/s effectives, temps passé en WaitVblank.
Croiser avec le desktop (`proof_cyc`, taux de dispatch headless) pour repérer
une régression de perf introduite par un dispatch.

### 8. Consigner (Table 3)
`date | commit | dispatches embarqués (IDs) | vitesse | fidélité | crash-free | notes`.
Lister les IDs `D<…>` embarqués (depuis `dispatch_all.c` au commit). Promouvoir
à **L4** les dispatches confirmés sans régression sur device.

### 9. Clôture
Mettre à jour le `[TASK:*]`, ADR/obstacles, diary. Si recovery nécessaire
(unité bricked), suivre `gnw-hardware:provision §4` puis re-tester.

---

## Garde-fous

- `SD_CARD=1` → `flash` ne fait **rien** silencieusement. Utiliser `SD_CARD=0`.
- `make clean` efface la ROM gitignorée → re-provisionner (§2).
- Vérifier la **SHA-1 ROM** identique à la cible RE.
- Power-cycle = vrai test de boot ; `disable-debug` peut bloquer la sonde
  jusqu'au power-cycle.
- **Fidélité par screenshot**, jamais par liveness seule (un rendu corrompu
  passe l'oracle de frames).
- Automatiser au maximum (GDB batch) ; réserver l'humain au câblage / power /
  lecture LCD.
