---
name: ff4-docs-sync
description: "Reconcile a session's work with the FF4 -> Game & Watch
  project's documentation, preserving the documentation architecture and
  anti-drift philosophy established in the 2026-07-04/05 docs overhaul
  (ff4/README.md + docs/primer/, ff4-port/docs/, ff4-gnw/docs/, the ADR
  backfill). Run at the end of any session that added a mechanism, made an
  architecture decision, fixed a bug with a generalizable lesson, or
  changed how a tool/workflow works — NOT for pure routine-porting
  progress (L1->L2->L3 promotions), which DISPATCH_REGISTRY.md already
  reflects without any docs edit needed. Also run on demand via
  /ff4-docs-sync, or delegate to the ff4-docs-syncer agent when the sync
  should happen without consuming the main conversation's context."
---

# ff4-docs-sync — keep the documentation honest, not just present

This project spent a full session building a didactic documentation layer
across all three repos, explicitly designed to avoid the two drift
failures already suffered twice before (French leaking into commits;
`reverser_hardcore.md` silently missing pitfalls `reverser_system.md`
had). That work has no value if the next ten sessions of real changes
don't get folded back into it — a documentation set that's accurate on
day one and stale by day thirty is worse than no documentation, because it
actively misleads. This skill is the reconciliation step.

**The default answer is "no docs change needed."** Most sessions produce
routine progress the generated registry already captures. Only run the
full procedure below when something happened that a reader of the
docs — the umbrella README, a repo's `docs/`, or an ADR — would need to
know to not be surprised or misled later.

---

## 1 — The documentation map: who owns which fact

Before writing anything, know where a given fact already lives (or should
live). Searching this map first is what prevents creating a second home
for something that already has one — exactly the mistake that produced
the `reverser_hardcore.md` drift and the two contradictory dispatch-count
lines fixed this week.

| Fact / topic | Owned by | Generated? |
|---|---|---|
| Dispatch mechanism definition, maturity ladder (L0-L4), 3-repo topology | `ff4/AGENTS.md` | No — hand-maintained, authoritative |
| Per-routine current level, dispatch counts by module | `ff4/DISPATCH_REGISTRY.md` Table 1 + distribution line | **Yes** — `registry/render_registry.py`, source `registry/dispatch_state.jsonl`. Never hand-edit; never re-quote a count elsewhere (link instead, see §3) |
| Step-by-step porting/validation/release procedure | `ff4/workflows/WF-{DECOMP,VALID,RELEASE}.md` | No — procedural, hand-maintained |
| SNES hardware / 65816 assembly / RE-methodology fundamentals for a total newcomer | `ff4/docs/primer/{00-04}*.md` | No — write once, update rarely (foundational content doesn't churn) |
| Known LLM-translation pitfalls (the numbered list) | `ff4-port/prompts/pitfalls.yaml` | **Yes** — rendered into `reverser_system.md`/`reverser_hardcore.md` by `prompts/generate_pitfalls.py`. Never hand-edit the `.md` prompt files' pitfalls section |
| Lasting architecture decisions (chose X over Y, will constrain future work) | `ff4-port/docs/adr/*.md` | No — one file per decision, write once |
| Why the translation pipeline / validation oracle work the way they do | `ff4-port/docs/architecture-overview.md`, `docs/workflow/{translation-cascade,validation-oracle}.md` | No |
| Why the dispatch integration / firmware constraints / build flags work the way they do | `ff4-gnw/docs/{dispatch-integration,firmware-and-hardware,build-and-flash-explained}.md` | No |
| Per-routine verified DP/DB entry-state facts | `ff4-gnw/CONVENTIONS.md` | No |
| Escalation triggers (when an agent should stop and hand off) | `ff4/workflows/ESCALATION.md` | No |
| Cross-session task state, obstacles, decisions-in-flight | MemPalace `wing=ff4-gnw` (`room=task-handoff`, `architecture-decisions`, `obstacles-and-solutions`) | No — this is working memory, not the versioned docs. See §5 for how it feeds this skill, not the other way around |

If you're about to write a fact that already has a row above, **update
that file** — do not add a second copy, even a "shorter, friendlier"
one, even in a different repo.

## 2 — The philosophy (carried over from the docs overhaul, do not violate)

- **One-writer rule.** Every fact lives in exactly one file. Everything
  else links to it. A README explains a topic in 2-3 sentences and links
  out — it never re-explains what `AGENTS.md`, a `workflows/*.md`, or an
  ADR already owns.
- **Docs are explanatory, never authoritative on mechanism.** `AGENTS.md`
  and the `workflows/` procedures remain the source of truth for *how the
  system behaves*. A `docs/` page earns its existence by explaining *why*,
  for a reader who needs the "why" to not get lost — it should not become
  a second, informally-authoritative description of the mechanism that
  can drift from the first.
- **Generic content lives once, in the umbrella.** SNES/assembly/RE
  fundamentals go in `ff4/docs/primer/`, referenced from `ff4-gnw` and
  `ff4-port` via **absolute** `https://github.com/hcross/ff4/blob/main/...`
  URLs — never copied into a submodule, which can be cloned standalone.
- **No duplicated numbers.** A count, a percentage, a status that's
  tracked and generated elsewhere (dispatch counts, pitfall counts,
  registry distribution) is never hand-typed a second time in a README or
  a docs page. Link to the generator's output instead. This was the exact
  bug fixed in `ff4-gnw/README.md` on 2026-07-05 (a stale "213 routines"
  line that didn't even agree with its own per-module breakdown).
- **Cross-repo links absolute, same-repo links relative.** Verify both
  kinds resolve before committing (see §4).
- **Backfilled ADRs are honest about being backfilled.** If a decision is
  documented after the fact, say so ("Note on backfilled ADRs" pattern in
  `ff4-port/docs/adr/adr-001-native-c-port.md`) and don't invent a
  discussion or a benchmark that isn't actually traceable to a real
  source — cite the *actual* file a number came from, not the file that
  seemed like it should have it (this exact mistake — misattributing a
  real, correct number to the wrong file — was caught by proofreading in
  the original docs session and is worth re-checking for every time).

## 3 — Procedure

### Step 1 — Gather what changed

If invoked at the end of an in-progress conversation, you already have
the session's history — use it. If invoked standalone (e.g. as the
`ff4-docs-syncer` agent, with no memory of the conversation that preceded
it), reconstruct it:

```sh
# Per repo (ff4, ff4-gnw, ff4-port): what's uncommitted, and what landed
# in the last session's commits (adjust the range to the actual session
# boundary — e.g. commits after the last "chore(submodules): bump" in the
# umbrella, which marks the end of the previous sync).
git status --short
git log --oneline <since>..HEAD
```

```
mempalace_search(query="[TASK", wing="ff4-gnw", room="task-handoff")
mempalace_search(query="[ADR]", wing="ff4-gnw", room="architecture-decisions")
mempalace_list_drawers(wing="ff4-gnw", room="obstacles-and-solutions")
```
Filter to drawers created since the last sync (`created_at`). These often
contain the *reasoning* behind a change that the git diff alone won't show
— exactly the material a docs update needs, not just "what changed" but
"why it matters to a future reader."

### Step 2 — Classify each substantive change

For each distinct thing that happened, walk this decision tree. Multiple
things can map to the same file — batch them into one edit, one commit.

1. **Is it a new, lasting architecture decision** (chose X over Y in a way
   that will constrain or guide future work)? → New ADR in the relevant
   repo's `docs/adr/`, following the existing template (Status/Date/
   Deciders/Scope, Context, Decision, Consequences, Alternatives
   rejected). If it's genuinely retroactive, mark it so.
2. **Is it a new or changed mechanism** (how the dispatch table, the
   translation pipeline, the validation oracle, or the firmware
   integration actually works)? → Update the existing `docs/` page that
   owns that mechanism (§1's map). Do not create a new page for an
   existing topic; do not let the page's explanation drift from what
   `AGENTS.md`/the workflow doc says happens.
3. **Is it a newly-discovered translation pitfall** (a class of asm->C
   translation mistake, not a one-off bug)? → Add it to
   `ff4-port/prompts/pitfalls.yaml`, then `generate_pitfalls.py --write`.
   Never hand-edit the rendered section in `reverser_system.md`/
   `reverser_hardcore.md`.
4. **Is it a newly-discovered SNES-hardware or 65816-assembly fact that a
   total newcomer would need** (not project-specific)? → Add it to the
   relevant `ff4/docs/primer/` page, in the same didactic register as the
   rest of that page (define before using, link out for the full
   reference, keep it short).
5. **Is it a correction to something the docs previously got wrong**
   (a broken link, a stale count, a misattributed citation)? → Fix in
   place; the commit message should say what was wrong and why, so future
   readers of `git log` understand it wasn't arbitrary churn.
6. **Is it routine porting progress** (a routine moved L1->L2, a new
   dispatch entry, a registry count changed)? → **No docs edit.**
   `DISPATCH_REGISTRY.md` already reflects it, generated. Adding a
   "current status" bullet anywhere else just creates a new place for that
   number to go stale.
7. **Is it an internal tooling change with no conceptual weight** (a
   script's flag renamed, a bug fixed with no generalizable lesson)? →
   No docs edit. The commit message and, if relevant, a MemPalace
   `obstacles-and-solutions` drawer are enough.

When in doubt between "needs docs" and "doesn't," default to **not**
writing something — per the opening of this skill, an unnecessary docs
edit is not neutral, it's a new thing that can go stale.

### Step 3 — Write, respecting the audience of the file you're touching

- `ff4/docs/primer/*` — assume **zero** prior background. Define every
  term before using it or link to where it's defined.
- `ff4-port/docs/*`, `ff4-gnw/docs/*` — may assume the primer was read.
  Still gloss unfamiliar project-specific terms inline (a short
  parenthetical or a link), don't suddenly drop into unexplained jargon.
- `docs/adr/*` — decision-record register (Context/Decision/Consequences/
  Alternatives rejected), not a tutorial. Cite real sources for any
  specific claim (a benchmark number, a historical event) — if you can't
  point to where a number comes from, don't state it with false precision.
- READMEs — index only. A new fact gets a link into the right `docs/`
  page, not an inline paragraph.

### Step 4 — Never hand-edit generated content

- `DISPATCH_REGISTRY.md` Table 1 / distribution line — only via
  `registry/registry_promote.py` (per-routine level changes) or by
  re-running `registry/render_registry.py` after `dispatch_state.jsonl`
  changes.
- `ff4-port/prompts/reverser_system.md` / `reverser_hardcore.md`'s
  `<!-- PITFALLS:GENERATED:* -->` block — only via
  `prompts/generate_pitfalls.py --write`, after editing `pitfalls.yaml`.

### Step 5 — Verify before committing

```sh
# Registry still in sync? (only if dispatch_state.jsonl or the registry
# were touched this session)
python3 registry/render_registry.py --check
python3 registry/migrate_registry.py --check

# Pitfalls still in sync? (only if pitfalls.yaml or the prompts were touched)
python3 ff4-port/prompts/generate_pitfalls.py --check

# Link-resolution sweep over whatever docs/README files you touched or
# added this sync (adapt the file list; see the docs-overhaul session's
# own verification script for the exact pattern: relative links resolved
# via os.path, external links spot-checked against known-good domains,
# never assumed).
```

Re-read anything you wrote as the audience it's meant for would (a total
newcomer for the primer, someone who's read the primer for the rest).
Confirm no French slipped in (this project's recurring failure mode,
independent of what language the conversation happened in) — grep for
French stopwords/accented characters if in doubt, don't just eyeball it.

**Do not trust your own recollection of a fact into a citation.** If a
docs edit is about to say "X is documented in file Y," grep file Y first
and confirm X is actually there — the fps-benchmark misattribution
caught during the original docs session (a real, correct number,
attributed to the wrong file) is exactly the failure mode this guards
against, and it survived first-draft writing undetected.

### Step 6 — Commit, push, bump — in dependency order

1. Commit and push each submodule (`ff4-gnw`, `ff4-port`) that changed,
   one commit per coherent change (not one giant commit per repo if
   several unrelated things changed — match this project's existing
   atomic-commit convention).
2. Only then, in the umbrella (`ff4`): commit any umbrella-level docs
   changes (`README.md`, `docs/primer/`) **together with** the submodule
   pointer bumps for whichever submodules changed, then push.
3. Confirm `git status` on all three repos shows only pre-existing,
   already-flagged residue (dirty vendored submodules, untracked
   regeneratable spike files) — never leave a real, new uncommitted change
   behind.

## 4 — What NOT to do

- Don't create a new `docs/` page for every commit — most sessions need
  zero docs changes (see the opening of §3).
- Don't touch `AGENTS.md`, `DISPATCH_REGISTRY.md`'s generated sections, or
  the prompts' generated pitfalls block by hand.
- Don't skip the verification step because "it's just a small wording
  change" — the two real bugs shipped in the original docs session (a
  broken relative link, a misattributed citation) were both exactly that
  kind of small, seemingly-safe edit.
- Don't invent a rationale for a backfilled decision that isn't traceable
  to something real (a commit, an existing doc, a measured number) — say
  "not evaluated" or "inferred, not directly evidenced" rather than
  fabricate confidence, exactly as `adr-002-lakesnes-upstream.md`'s
  "Alternatives rejected" section does for the one alternative that
  genuinely wasn't part of this project's own history.
- Don't duplicate a count/status number that's generated elsewhere, even
  "just this once" — that's precisely how the `ff4-gnw/README.md`
  213-vs-240 contradiction happened.

## 5 — MemPalace stays working memory, not a second docs copy

MemPalace's `task-handoff`/`architecture-decisions`/`obstacles-and-solutions`
drawers are session-to-session working memory — they're where this skill
*looks* for what happened and why, not another place to *write* the
didactic explanation. Once a decision from an `architecture-decisions`
drawer has been promoted to a real ADR file, the MemPalace drawer doesn't
need to be deleted, but don't keep elaborating it in parallel with the
ADR — the ADR is now the durable, versioned copy; the drawer is history.

At the end of a sync, update (don't replace) the relevant
`[TASK:ongoing]`/`[TASK:checkpoint]` drawer to note that a docs sync
happened and what it covered — this closes the loop for whoever resumes
next, the same way this project's session-start protocol
(`AGENTS.md` §B.4) already expects.

## 6 — Worked examples to match the style against

Before writing new prose, skim one existing file of the same kind to
match tone and structure:

- Primer page: `ff4/docs/primer/02-65816-assembly-101.md`
- Repo-specific deep dive: `ff4-port/docs/workflow/validation-oracle.md`
- ADR: `ff4-port/docs/adr/adr-003-classification.md`
- README pointer (the "index, not content" pattern):
  the "New to reverse engineering..." callout near the top of
  `ff4-port/README.md` or `ff4-gnw/README.md`.
