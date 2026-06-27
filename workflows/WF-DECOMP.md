# WF-DECOMP — Décompilation & validation formelle d'une routine

> Transformer une routine ASM 65816 en C natif équivalent, **prouvé** par
> recompilation bit-à-bit et tests unitaires aux limites. Produit un dispatch au
> niveau **L2**. Pré-requis du workflow [WF-VALID](WF-VALID.md) (qui le pousse
> en L3).

**Skill principal** : `snes-re:asm-to-c-port` (+ `snes-re:snes-asm`,
`snes-re:disasm-trace`). **Agent** : `snes-reverse-engineer`.

---

## Entrée

- Une adresse SNES cible (ex. `$03:9E85`) → ID `D039E85`.
- Le désassemblage de référence : `ff4-port/upstream/notes/ff4j-sfc.asm`.
- La ROM (vérité des octets) : `ff4-port/upstream/rom/ff4-jp1.sfc`.

## Sortie

- Un fichier C `ff4-gnw/<domaine>/<Nom>.c` avec la routine portée.
- Une entrée à jour dans [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 1.
- *(quand l'infra existe)* un test unitaire C + son équivalent ASM c65.

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

### 3. Produire le C (sequential-thinking pour le raisonnement)
- Une fonction C par routine ASM ; **adresse ROM d'origine en commentaire**.
- Variables aux **adresses WRAM d'origine** (`snes->ram[...]`).
- Flux de contrôle irréductible → transcrire en `goto`+labels **fidèlement
  d'abord**, refactor ensuite.
- Tables ROM locales → `static const` en tête de fichier.
- `adc/sbc` → `+/-` ; un carry/garbage entrant relevé = bug d'origine à traiter
  explicitement (patch ROM côté harness), pas à répliquer silencieusement.
- **Synchroniser les registres CPU avant tout `run_emulated_func`** : si l'ASM
  fait `LDA $xx` avant un `JSR`, poser `cpu->a` avant l'appel (cause du bug F12).

### 4. Recompilation ASM c65 + comparaison bit-à-bit ⚠ *(infra à construire)*
> Cette étape n'est **pas encore implémentée**. Cible :
> 1. Recompiler la routine C en 65816 via un toolchain c65.
> 2. Comparer **octet par octet** le binaire produit avec la plage ROM d'origine
>    (ou son équivalent fonctionnel après normalisation des adresses).
> 3. Tout écart = soit un bug de port, soit un bug d'origine documenté (patch
>    ROM assert-guardé côté harness).
>
> Tant qu'absente, une routine plafonne à **L1** sur le critère décompilation
> et ne peut atteindre L2 que par les tests unitaires (étape 5) seuls — à
> marquer explicitement dans le registre. Chantier suivi dans [BACKLOG.md](../BACKLOG.md).

### 5. Tests unitaires aux limites (C + ASM c65) ⚠ *(infra à construire)*
> Cible : pour chaque routine, des cas aux limites (0, valeurs max, carry
> entrant, débordements, indices extrêmes) exécutés **en C** et **en ASM c65**,
> avec comparaison des sorties (WRAM ciblée + registres). Valide le comportement
> aux frontières que l'oracle in-game ne couvre pas forcément.

### 6. Consigner dans le registre
Mettre à jour [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 1 :
`ID | adresse | routine | domaine | niveau | notes`. Niveau atteint :
- **L1** si seul le corps C est écrit ;
- **L2** si tests unitaires C+ASM passants (et idéalement recompil bit-à-bit OK).

### 7. Clôture
Mettre à jour le `[TASK:*]` (→ `checkpoint` si on continue, `done` sinon).
Consigner toute découverte non triviale en ADR (`room=architecture-decisions`)
ou obstacle (`room=obstacles-and-solutions`). Écrire une entrée de diary.

---

## Garde-fous

- **Direct-page d'abord** (§1) — la cause n°1 des bugs FF4.
- **Octets ROM = vérité** (§2).
- **Synchroniser les registres CPU avant `run_emulated_func`** (§3, leçon F12).
- Une routine n'est **jamais** L3 ici — c'est le rôle de [WF-VALID](WF-VALID.md).
- Ne pas porter plus d'une routine à la fois sans la rendre vérifiable.
