# REPRISE — Reset sélectif des assets

> Le projet est dans un état **instable** : des corrections successives ont été
> empilées sans qu'on sache toujours quelle correction compense quoi. Cette
> reprise vise à repartir sur une base **structurée** sans jeter les
> enseignements acquis.

**Principe** : pas un repartir de zéro total, mais un **reset sélectif par
couche**. On garde le prouvé, on remet en interpréteur le non-prouvé, on
requalifie dans l'ordre via [WF-DECOMP](workflows/WF-DECOMP.md) +
[WF-VALID](workflows/WF-VALID.md).

---

## Stratégie

1. **Garder** les dispatches L3/L4 (validés oracle ou device).
2. **Remettre en interpréteur pur** tout dispatch L0/L1 non prouvé qui introduit
   un risque de dérive — quitte à perdre temporairement le gain de perf.
3. **Requalifier** chaque routine L1 → L2 → L3 dans l'ordre de priorité, une à
   la fois, en consignant le résultat dans [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md).
4. **Documenter** chaque décision de garder/retirer/requalifier, pour ne plus
   jamais perdre le « pourquoi ».

> ⚠ État de départ honnête : **le registre est marqué L1 par défaut** (sauf 1
> stub L0) — prudence, pas vérité. L'infra d'équivalence runtime existe déjà
> (spikes `parity/` + oracle), et l'historique de spikes (juin) montre que
> beaucoup de routines ont déjà une équivalence runtime par routine. L'audit
> consiste à **créditer** ces validations (→ L2) et à mener les manquantes en
> L2/L3, pas à tout refaire de zéro. (Pas de recompilation bit-à-bit : voie
> abandonnée — cf. [AGENTS.md](AGENTS.md) §B.2.)

---

## Audit de classification (FAIT — 2026-06-27)

Voir [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md). Distribution :
**L0=1 · L1=56 · L2=141 · L3=5 · EXCL=3**. 134 routines promues L1→L2 par spike
batch (équivalence runtime fuzzée). 2 FAIL isolés (`CheckMenu_c`, `TfrBGAnimGfx_c`).

## Décision de stabilisation (étape 3 — 2026-06-27)

> **Conclusion : aucune réversion.** L'audit a invalidé la prémisse initiale de la
> REPRISE (« reverser les L0/L1 non prouvés pour regagner une base saine »). Avec
> 146 routines prouvées (L2+L3) et seulement 2 divergences réelles isolées, la
> base est **déjà stable**. Surtout, **reverser n'est ni gratuit ni toujours sûr** :

- **DMA** : reverser une routine DMA vers le chemin interpréteur **hardfault
  post-savestate sur device** (F3). `TfrBGAnimGfx_c` (1 des 2 FAIL) est une
  routine DMA (`output_ram` = `$43xx`/`$420B`/`$211x`) → **NE PAS reverser**.
- **WaitVblank / NMI** : certaines routines sont dispatchées *parce que* le chemin
  interpréteur boucle ou est trop lent (cf. F10). Les reverser réintroduit le hang.
- **Input (F5)** : `UpdateCtrlField_ext` & co. sont des réimplémentations
  intentionnelles incompatibles avec le harness en interpréteur.

Décision par catégorie :

| Catégorie | Nb | Décision | Pourquoi |
|-----------|----|----------|----------|
| L2 (spike) + L3 (oracle) | 146 | **garder** | équivalence prouvée |
| EXCL (DMA-bypass) | 3 | **garder** | divergence intentionnelle, device-safe |
| L0 stub (`ExecSound_ext_stub`) | 1 | **garder** | stub délibéré (débloque le titre) |
| FAIL `CheckMenu_c` (D0081F4) | 1 | **garder + investiguer** | 1/400, flux sur entrée rare — artefact probable (WF-VALID) |
| FAIL `TfrBGAnimGfx_c` (D00CB5F) | 1 | **garder + investiguer** | DMA → revert dangereux ; 2/400 |
| L1 build_error | 35 | **garder** | non-spikable ≠ cassé ; rendre le spike self-contained |
| L1 no_source (btlgfx) | 11 | **garder** | corps bundlés ; spike custom requis |
| L1 no_contract | 8 | **garder** | ajouter un bloc CONTRACT puis spiker |

L'effort se **réoriente** : de « reverser » vers « fermer les 56 L1 » (fixer les
build_error, spiker les btlgfx, investiguer les 2 FAIL). C'est la vraie suite.

## Ordre de priorité — chemin critique combat

La reprise suit le flux de jeu le plus impactant (combat), de la racine vers les
feuilles :

1. **Timers ATB** — `D039741` GetPendingAction, `D039788` CheckTimer,
   `D0397B3` InitAction, `D039E65/E71/F1C/F75` TimerDur, `D039FD8` ApplySpeedMod
   *(arc F11/F12 — à confirmer en L3 par WF-VALID isolé)*
2. **Actions & commandes** — `Cmd_*`, `do_*_emu` (actuellement no-op → dégâts
   avalés, animations manquantes)
3. **IA monstre** — `RandAITarget_emu`, `SkipAITurn_emu`, `AITarget_*`, `AICond_*`
   *(bug observé : monstres passifs en dispatch)*
4. **Effets magiques** — `MagicEffect_*`, `MagicDmgEffect`
5. **Graphismes de combat** — `D038085` ExecBtlGfx, btlgfx monsters, `D03FE03`
   TfrSprites
6. **Retour field** — routines `field` du chemin de sortie de combat

## Suivi de requalification

| Lot (date) | Action | Détail |
|------------|--------|--------|
| Spike batch 2026-06-27 | requalifier | 134 × L1→L2 (équivalence runtime fuzzée) |
| Étape 3 2026-06-27 | garder | 0 réversion (base stable ; revert DMA/WaitVblank dangereux) |

**Actions possibles** : `garder` (déjà prouvé / revert risqué) · `requalifier`
(L1→L2/L3 via workflows) · `retirer` (remettre en interpréteur — **seulement si
sûr** : pas DMA, pas WaitVblank, pas input) · `porter` (stub → C réel).

---

## Lien avec l'investigation en cours

Le bug combat documenté dans MemPalace (`[TASK] ff4-combat-visual-bugs` :
animations d'attaque absentes + monstres passifs en natif) est un **symptôme**
de l'état instable. Sa résolution passe par la requalification des couches 2 et 3
ci-dessus (actions/commandes et IA monstre), pas par un patch ponctuel de plus.
