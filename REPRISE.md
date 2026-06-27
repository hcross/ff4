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

> ⚠ État de départ honnête : **les 206 dispatches sont à L1** (sauf 1 stub L0).
> Aucun n'a traversé la chaîne formelle complète (recompil ASM c65 + tests
> unitaires + oracle isolé), même si certains ont des findings oracle partiels.
> La reprise consiste précisément à transformer ce « L1 par défaut » en niveaux
> **mérités**.

---

## Audit de classification (à mener)

Pour chacun des 206 dispatches, statuer sur l'état **réel** :

- [ ] Classer en L0 / L1 / L2 / L3 / L4 selon les critères AGENTS §B.2
- [ ] Identifier les **stubs no-op résiduels** dans la table (corps vide ou
      `_emu` no-op appelé) — candidats au retrait immédiat
- [ ] Repérer les **corrections de compensation** (un fix qui masque un autre
      bug) — à dé-corréler
- [ ] Marquer les dispatches **à DMA-bypass intentionnel** (exclus baseline :
      `D15CADC`, `D048004`, `D03FE03`, `D15CA5E`) — statut spécial, pas L3 au
      sens strict

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

| Routine (ID) | Niveau avant | Action | Niveau après | Date | Réf |
|--------------|--------------|--------|--------------|------|-----|
| _(à peupler au fil de la reprise)_ | | | | | |

**Actions possibles** : `garder` (déjà prouvé) · `requalifier` (L1→L2/L3 via
workflows) · `retirer` (remettre en interpréteur) · `porter` (stub → C réel).

---

## Lien avec l'investigation en cours

Le bug combat documenté dans MemPalace (`[TASK] ff4-combat-visual-bugs` :
animations d'attaque absentes + monstres passifs en natif) est un **symptôme**
de l'état instable. Sa résolution passe par la requalification des couches 2 et 3
ci-dessus (actions/commandes et IA monstre), pas par un patch ponctuel de plus.
