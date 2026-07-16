# Dispatch address ranges — `dispatch_ranges.json` + `extra_ranges.json`

These two files give a later **impact tool** (Phase 3) the SNES byte extent of
every dispatched routine, so it can intersect those extents with the modified
byte ranges of a translation patch and decide which dispatches to **gate**
(fall back to the interpreter) when running on a non-vanilla ROM.

`registry/dispatch_state.jsonl` stores only routine **entry PCs**. These files
add the **extents**. They are the read-only inputs to Phase 3; do not hand-edit
the generated one.

---

## `dispatch_ranges.json` — GENERATED

One entry per row of `dispatch_state.jsonl` (all levels: L0–L4, DELEG, EXCL,
RETIRED — the `level` is carried through so Phase 3 can filter). Regenerate with:

```sh
python3 registry/gen_ranges.py            # rebuild if needed, write the file
python3 registry/gen_ranges.py --check    # drift check, exit 1 on mismatch
python3 registry/gen_ranges.py --rebuild  # force the out-of-band assemble+link
```

### How the extents are derived (and proven against the true ROM)

The buildable reference disassembly lives in the vendored `ff4-port/upstream`
submodule. `dispatch_state.jsonl` has no extents, the vendored objects were
assembled without `-g` (no symbol records), and the VICE label dump
(`ld65 -Ln`) only carries the ~40 exported symbols — far too few to bound ~215
routines. So `gen_ranges.py` performs an **out-of-band** build in a gitignored
scratch dir (`registry/.ranges-build/`), never touching the vendored tree:

1. Re-assemble each module with `ca65 -g` and the exact jp1 flags
   (`-D BUGFIX_WORLD_BATTLE=1 -D ROM_VERSION=1`) into the scratch dir.
2. Re-link with `ld65 --dbgfile`, reusing the vendored `ff4-jp.lnk` config.
3. **Prove** the relinked image against the tracked `rom/ff4-jp1.sfc`: the only
   bytes allowed to differ are the 4-byte internal-header checksum pair (file
   `0x7FDC–0x7FDF`); every other byte must be byte-identical. That proves the
   label addresses are computed against the true ROM bytes. Those 4 bytes are
   then copied from the tracked ROM so the scratch image CRC32 == `CAA15E97`.

`-g` changes only the object's debug records, never the emitted bytes, so the
proof holds. This is why we use `ld65` labels and **not** the annotation
comments in `notes/ff4j-sfc.asm` (those drift +2 on ~6 routines and omit banks
08/0E/12/1E). The scratch dir is disposable; delete it and it is rebuilt on the
next run. Requires `ca65`/`ld65` (cc65 suite) on `PATH`; **no** Node dependency
(the checksum is copied from the tracked ROM, not recomputed).

### Boundary policy

A routine's range is `[entry, next_label − 1]`, where `next_label` is the
nearest **routine-level** label strictly after the entry **in the same bank**.
Routine-level = a named (non-`@`-prefixed) `lab` symbol. The `@`-prefixed
*cheap-local* labels are intra-routine branch targets; bounding by them would
undershoot the routine end catastrophically (e.g. `DrawNpcs` would be 6 bytes
instead of 584). If no later label exists in the bank, the end falls back to the
bank top (`$bb:FFFF`) — an **overshoot**, which is the safe direction.

Each entry carries: `start`/`end` (SNES `bbaaaa` hex, matching the `pc`
convention), `file_start`/`file_end` (flat `.sfc` file offsets, the primary
intersection keys), `resolved`, and `source_label` (the asm label the range was
anchored to — provenance; note the asm name differs from the registry's C-port
name, e.g. `DrawNPCs` vs `DrawNpcs_c`).

Top-level `"slop": 4` is the **±4-byte tolerance** the impact tool may apply to
each bound rather than silently widening here. It absorbs the residual ±2
annotation drift so a patch byte landing within 4 bytes of a bound is still
caught.

### The always-gate policy — `resolved`

`resolved` is `true` **iff the entry PC sits exactly on a routine-level label**.
This is stricter than "the PC falls inside some label's range", on purpose: it
fails closed.

`resolved: false` entries are of three kinds (see the audit numbers below):
uncorrected ±2 annotation drift (the registry PC is 2 off the true label), code
embedded in a data-labeled region (banks 08/0E/12/15/16/1E, where the disasm
labels tilemaps / event-scripts / battle-props, not the code), and RETIRED /
dead entries (e.g. `D00F533`, a mid-operand address that is not an instruction
boundary). They still carry a **best-effort containing range** as a hint (65 of
67 do; 2 in bank 08 have no same-bank predecessor label and are fully bare with
`null` bounds).

> **Phase 3 MUST always-gate every `resolved: false` entry**, ignoring its hint
> range. Gating a dispatch means disabling the C port and running the
> interpreter over the (patched) ROM bytes — which is correct for *any* ROM,
> so this is unconditionally safe regardless of the hint's accuracy. The hint
> range exists only for diagnostics / future tightening.

### De-gating a `resolved: false` entry (manual, rare, evidence-required)

Someone MAY decide a `resolved: false` entry's fail-closed gating is overly
conservative for a specific variant — e.g. `registry/VARIANT_GAPS.md`'s "cheap,
high-yield remedy" of pinning the range manually and re-running
`registry/patch_impact.py` so the entry moves to the not-gated set. That
change is real (it un-gates a routine on-device) and cannot rest on the pin
alone:

1. Pin the range (either fix the underlying resolution so `gen_ranges.py`
   resolves it naturally, or add a manual entry `patch_impact.py` can
   consult — do not silently widen the fail-closed hint).
2. Re-run `registry/patch_impact.py`; confirm the entry now shows as
   not-gated for the variant.
3. **Mandatory, not opportunistic** (unlike ordinary WF-VALID variant
   passes, see workflows/WF-VALID.md step 1): run
   `python3 ff4-port/patches/spike_check.py D<id> --variant <id>` AND an
   oracle isolation pass on the variant's canonical image (capture a
   dedicated seed if none reaches the routine yet). Both must pass before
   the de-gating is trusted.

De-gating is a deliberate, rare, human claim about the patched asm; it must
carry its own fresh evidence rather than ride on whatever the opportunistic
spike/oracle catalogue already happens to cover.

---

## `extra_ranges.json` — MANUAL

Records ROM data regions that a dispatched C body has **frozen a copy of**
(a `static const` array copied verbatim from ROM) that lie **outside** that
dispatch's own code range. Such a copy goes stale if the patch rewrites the
source bytes, yet the dispatch's code range shows no overlap — so the impact
tool must gate the listed `dispatch_id` on any intersection with these ranges.

Schema: `{"entries": [{"dispatch_id": "D…", "reason": "…", "ranges":
[{"start": "bank:addr", "end": "bank:addr"}]}]}` (plus provenance keys a
tolerant parser ignores). If a copied table's ROM address cannot be pinned
confidently, record it with `"ranges": []` and `"unresolved": true` — fail-closed
(the impact tool always-gates it).

### Audit method & date

**2026-07-15.** Grepped `ff4-gnw/{battle,field,menu,cutscene,sound}/` and
`ff4_helpers.c` for `static const`. 15 files carry one. Each was classified by:
(a) is the array actually **read** by the body? (b) copied-from-ROM vs
algorithmic? (c) does the ROM source lie **outside** the dispatch's own code
range? ROM addresses were pinned by **unique byte-search** against
`ff4-port/upstream/rom/ff4-jp1.sfc` (CRC32 `CAA15E97`).

**Recorded (2):**

| dispatch | table | ROM range | why it is not covered by the code range |
|----------|-------|-----------|------------------------------------------|
| `D00BB6A` (`DrawNpcs_c`) | 4 walk-cycle anim tables | `$00:BDF8–$00:BE0F` | tables sit past the routine's code end (`$00:BDB1`) |
| `D0387D8` (`CheckFanfare_c`) | `NoFanfareTbl` (battle msg-IDs) | `$13:FE67–$13:FE75` | separate data table in bank 13; consumed via pointer/delegate + a (currently unwired) frozen helper `NoFanfareTbl_c` |

**Excluded, with rationale:**

- **Algorithmic constants** — `Pow10Hi` (powers of ten, `D15C37F`) and
  `UpdateBG2Scroll`'s `k_speed_mask` / `k_h_delta` / `k_v_delta` (scroll masks
  and direction deltas). Not ROM copies.
- **Dead no-op data-label stubs** — `GilWindowTiles4`, `LavaAnimPal`,
  `MapTitleTilesTop`/`Btm`, `WipeScanlineTbl`, `DlgTilesTop`, `PlayerSpriteTiles`,
  `LoadBattleSpeedPosText`, `_15bb6a`, `_15b8c9`. Each is a dispatch whose body
  is a literal no-op; the `static const` is declared but **never read**, and the
  dispatch's own range already covers its data. (PITFALL 11: "data-only label
  handled as static const array and stub".)
- **Unwired dead helper** — `cutscene/_13e4f2.c` (`_13e4f2_c`, a symmetric
  32-byte brightness ramp at `$13:E4F2–$13:E511`). The array *is* read, but the
  `static` helper has **no caller** anywhere in the tree, so no live dispatch
  depends on it. Address pinned here for the day it gets wired; not an active
  dependency.

---

## For the Phase 3 impact tool

- Intersect a patch's modified file-offset ranges against
  `dispatch_ranges.json[*].file_start..file_end` (optionally widened by `slop`)
  **and** `extra_ranges.json[*].ranges` (convert `bank:addr` via LoROM
  `file = (bank<<15) | (addr & 0x7fff)`).
- **Always-gate** every `resolved: false` dispatch and every `extra_ranges`
  entry marked `unresolved: true`, independent of intersection.
- Filter by `level` as needed (RETIRED/EXCL are carried for completeness).
- Both files are deterministic (entries sorted by PC) so diffs stay stable.
