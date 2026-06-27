# WF-DECOMP — Décompilation & équivalence runtime d'une routine

> Transformer une routine ASM 65816 en C natif équivalent, **prouvé par
> équivalence runtime par routine** (le harnais *spike* : C vs asm-interprétée à
> état d'entrée identique). Produit un dispatch au niveau **L2**. Pré-requis du
> workflow [WF-VALID](WF-VALID.md) (qui le pousse en L3 par validation en jeu).
>
> ⚠ La preuve n'est **pas** une recompilation bit-à-bit du C en ASM c65 — voie
> abandonnée (cc65 cible le 6502, pas le 65816 ; jamais d'égalité d'octets avec
> l'asm écrit à la main). La preuve est *runtime*, comme zelda3/snesrev.

**Skill principal** : `snes-re:asm-to-c-port` (+ `snes-re:snes-asm`,
`snes-re:disasm-trace`). **Agent** : `snes-reverse-engineer`.
**Outils** : `ca65-bridge` (extraction/classification asm), `translator/`
(traduction LLM asm→C), `parity/` (`generate_spike.py`, `ff4-spike-*`,
`ff4-parity-compare`).

---

## Entrée

- Une adresse SNES cible (ex. `$03:9E85`) → ID `D039E85`.
- Le désassemblage de référence : `ff4-port/upstream/notes/ff4j-sfc.asm`.
- La ROM (vérité des octets) : `ff4-port/upstream/rom/ff4-jp1.sfc`.

## Sortie

- Un fichier C porté : d'abord `port/<module>/<func>.c` (zone de traduction),
  promu ensuite vers `ff4-gnw/<domaine>/<Nom>.c` une fois le spike vert.
- Un spike d'équivalence runtime (`parity/src/spike__<addr>_*.c`) qui passe.
- Une entrée à jour dans [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 1.

---

## Étapes

### 0. Rétablissement de contexte
Appliquer le **protocole post-compaction** (AGENTS §B.4). Ouvrir/poser un
`[TASK:ongoing] wf-decomp-D<id>` dans MemPalace `wing=ff4-gnw, room=task-handoff`.
Lancer une séquence **sequential-thinking** dédiée à cette routine.

### 1. Résoudre le direct-page (étape zéro de TOUTE routine)
Déterminer `D / m / x / DB` à l'entrée. Tout `$nn` est `[D + nn]`, pas `$00nn`.
Identifier les appelants pour connaître `D` (FF4 field/NMI : `D=$0600`).
**Consigner** `D/m/x/DB` en commentaire d'en-tête du futur fichier C.

### 2. Lire l'ASM et les octets ROM
Lire la routine dans `ff4j-sfc.asm`. Vérifier chaque cible de `jsr/jsl/jmp`
**par les octets ROM**, pas par les labels du désassemblage. Suivre les flags
m/x (REP/SEP) pour dimensionner immédiats et longueurs d'opcodes.

### 3. Produire le C (manuel ou assisté LLM)
Deux voies, même contrat de sortie (`port/<module>/<func>.c`) :
- **Manuelle** : porter à la main, avec `sequential-thinking` pour le raisonnement.
- **Assistée** : `translator/batch_translate.py` (provider LLM enfichable :
  claude-cli / anthropic-sdk / openai-compat) traduit l'asm → C, après
  classification translate/delegate par `ca65-bridge classify`. Toujours commencer
  par `--dry-run`, plafond `--budget-usd`.

Règles de port (identiques dans les deux voies) :
- Une fonction C par routine ASM ; **adresse ROM d'origine en commentaire**.
- Variables aux **adresses WRAM d'origine** (`snes->ram[...]`).
- Flux de contrôle irréductible → transcrire en `goto`+labels **fidèlement
  d'abord**, refactor ensuite.
- Tables ROM locales → `static const` en tête de fichier.
- `adc/sbc` → `+/-` ; un carry/garbage entrant relevé = bug d'origine à traiter
  explicitement (patch ROM côté harness), pas à répliquer silencieusement.
- **Synchroniser les registres CPU avant tout `run_emulated_func`** : si l'ASM
  fait `LDA $xx` avant un `JSR`, poser `cpu->a` avant l'appel (cause du bug F12).

### 4. Équivalence runtime par routine — le spike *(infra EXISTANTE)*
> **Note méthodo (ADR à acter).** La cible initiale « recompiler le C en ASM c65
> et comparer bit-à-bit à la ROM » est **abandonnée** : elle est inatteignable
> par construction (cc65 cible le 6502, pas le 65816, et ne reproduit jamais
> l'asm FF4 écrit à la main). La **vraie** preuve d'équivalence est *runtime*,
> exactement comme zelda3/snesrev — et elle est déjà outillée.

Générer et lancer le spike de la routine :
```sh
python translator/generate_spike.py port/<module>/<func>.c   # → parity/src/spike__<addr>_*.c
cd parity && make ff4-spike-<nom> && ./ff4-spike-<nom> ../upstream/rom/ff4-jp1.sfc [frames]
```
Le spike inline le C porté et le compare, **à état d'entrée identique**, contre
`run_emulated_func` (l'asm originale exécutée dans l'interpréteur) : même état
WRAM/registres en entrée → exécuter C *vs* asm → comparer l'état de sortie.
Vert ⇒ équivalence runtime de la routine prouvée. Le `ca65` (suite cc65,
installé) sert au sous-module `upstream` à **réassembler le désassemblage en ROM
vanilla de référence** (la ROM « or » de `parity_compare`), pas à recompiler le C.

### 5. Couverture aux limites *(à formaliser sur la base des spikes)*
Le spike couvre l'état atteint par la/les savestate(s) de test. Pour les **cas
aux limites** (0, valeurs max, carry entrant, débordements, indices extrêmes)
que ces états ne traversent pas forcément : étendre le harnais de spike pour
injecter des états d'entrée synthétiques avant l'appel et comparer les sorties
C vs interpréteur. C'est une **extension** de l'infra spike existante
(`generate_spike.py`), pas une chaîne ASM séparée. Suivi dans [BACKLOG.md](../BACKLOG.md).

### 6. Consigner dans le registre
Mettre à jour [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 1 :
`ID | adresse | routine | domaine | niveau | notes`. Niveau atteint :
- **L1** si seul le corps C est écrit (non validé) ;
- **L2** si le spike d'équivalence runtime passe (et, à terme, couverture aux
  limites de l'étape 5).

### 7. Clôture
Mettre à jour le `[TASK:*]` (→ `checkpoint` si on continue, `done` sinon).
Consigner toute découverte non triviale en ADR (`room=architecture-decisions`)
ou obstacle (`room=obstacles-and-solutions`). Écrire une entrée de diary.

---

## Garde-fous

- **Direct-page d'abord** (§1) — la cause n°1 des bugs FF4.
- **Octets ROM = vérité** (§2).
- **Synchroniser les registres CPU avant `run_emulated_func`** (§3, leçon F12).
- **Preuve = équivalence runtime (spike), pas recompilation bit-à-bit** (§4).
- Une routine n'est **jamais** L3 ici — c'est le rôle de [WF-VALID](WF-VALID.md).
- Ne pas porter plus d'une routine à la fois sans la rendre vérifiable.
