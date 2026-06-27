# WF-VALID — Validation comportementale en jeu

> Prouver qu'un dispatch produit le **même comportement** que l'interpréteur
> dans une situation de jeu réelle, en l'isolant dans l'oracle. Pousse un
> dispatch de **L2 → L3**.

**Outils** : `ff4-port/desktop/` (`ff4-desktop-oracle`, `wram_diff`,
`ff4-desktop-headless`, `proof_cyc`), `gnw-hardware:debug` (GDB si trace fine).

---

## Entrée

- Un dispatch déjà porté (idéalement L2) — ID `D<bank><addr>`.
- Une hypothèse sur l'endroit du jeu où la routine est sollicitée.

## Sortie

- Une ligne dans [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 2 :
  savestate, frames, CRC WRAM natif/interp, dérive, PC final, maturité.
- Promotion à **L3** si dérive nulle (hors masque stack) et pas de divergence
  d'exécution.

---

## Étapes

### 0. Rétablissement de contexte
Protocole post-compaction (AGENTS §B.4). `[TASK:ongoing] wf-valid-D<id>`.

### 1. Identifier le point d'usage
Déterminer une scène où la routine est appelée. Croiser avec
`KNOWN_FINDINGS.md` et le `miss_profiler` (PC chauds). Lister les savestates
de référence (`ff4-port/*.lss`) ; à défaut, en capturer un via
`ff4-desktop-sdl` (`5` = save slot incrémental).

### 2. Charger une savestate menant au moment d'usage
La savestate doit aboutir à un instant où **seul ce dispatch** importe. Vérifier
que la routine est bien atteinte :
```sh
./ff4-desktop-headless $ROM --load <scene>.lss --frames N --trace-frame F
# ou watch d'une adresse écrite par la routine :
./ff4-desktop-headless $ROM --load <scene>.lss --frames N --watch-wram <ADDR>
```

### 3. Isoler le dispatch dans l'oracle
Activer **uniquement** la routine cible, exclure tout le reste via le filtre
d'exclusion de l'oracle (`--exclude HEX`, répétable), ou inversement partir de
`oracle-baseline` et réintroduire la seule routine testée.
```sh
cd ff4-port/desktop
make oracle SEED=../<scene>.lss FRAMES=600        # A/B dispatch vs interpréteur
```

### 4. Comparer WRAM (CRC + diff byte-exact)
```sh
./wram_diff $ROM ../<scene>.lss        # diff byte-exact, masque la région stack
```
- **0 octet divergent** (hors masque) → fidèle.
- Divergence avec **delta de cycles ~0** mais PC à 1 instruction d'écart →
  **artefact de déphasage** (AGENTS §A.2), non significatif : vérifier par
  `wram_diff` (byte-exact), pas par le CRC par frame.
- Divergence réelle → étape 5.

> ⚠ **Comparer à `frames_run` SNES égal**, pas à frames headless égal :
> l'interpréteur est ~6× plus lent (AGENTS §A.2). Aligner les deux passes sur
> le même `frames_run` (lu dans la sortie `=== result ===`).

### 5. Validation visuelle (obligatoire pour le rendu)
Pour toute routine touchant l'affichage : dump frame + **pixel-diff** contre une
référence connue.
```sh
./ff4-desktop-headless $ROM --load <scene>.lss --frames N --out /tmp/cap.ppm
# convertir + comparer (sips → png, diff visuel)
```
Un rendu corrompu **n'est pas** détecté par fps/compteur de frames/fault seuls
(règle `snes-re` §6). Ne jamais conclure « OK » sur la seule absence de crash.

### 6. Trace fine si divergence (instrumentation)
- `--trace-frame F` pour lister les PC dispatchés à la frame divergente.
- `printf` embarqué dans la routine C (le write-hook WRAM est aveugle au C).
- `proof_cyc` pour la progression PC/cycles frame par frame.
- Sur device : `gnw-hardware:debug` (GDB, oracle liveness, SCB/CFSR).
- Lire les **premières adresses divergentes** de `wram_diff` → pointe le bug.

### 7. Consigner dans le registre (Table 2)
`ID | savestate | frames | CRC natif | CRC interp | dérive | PC final | maturité | date`.
Promotion **L3** si dérive nulle et exécution alignée. Sinon, rester au niveau
courant et ouvrir un obstacle MemPalace + (si pertinent) un finding dans
`KNOWN_FINDINGS.md`.

### 8. Clôture
Mettre à jour le `[TASK:*]`, ADR/obstacles, diary.

---

## Garde-fous

- **Isoler** : un seul dispatch actif, sinon la dérive n'est pas attribuable.
- **`frames_run` SNES égal** pour toute comparaison (pas frames headless).
- **Screenshot pixel-diff** pour tout rendu, jamais fps/frames/fault seuls.
- **`wram_diff` byte-exact** fait foi, pas le CRC par frame (artefacts).
- Le masque stack est légitime ; toute autre exclusion doit être **commentée**.
