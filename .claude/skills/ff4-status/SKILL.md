---
name: ff4-status
description: "Session bootstrap and health check for the FF4 -> Game & Watch
  port. Activate at the start of any session working in this repo, and after
  any compaction, before touching a dispatch, a spike, or the registry. Runs
  a scripted check (paths resolve, registry is in sync, ROM present) and
  prints the next actionable work from the registry — replaces manually
  reading DISPATCH_REGISTRY.md + BACKLOG.md + REPRISE.md + MemPalace to
  figure out where to resume."
---

# ff4-status — orientation and health check

Run this **before** starting any FF4 work, and again after a context
compaction. It replaces the manual join of DISPATCH_REGISTRY.md +
BACKLOG.md + REPRISE.md + MemPalace that the original acceleration audit
identified as the main cold-start cost.

## 1 — Health check (run these; expect all to succeed)

```sh
# From the umbrella repo root (ff4/):

# Registry in sync with its own generated sections?
python3 registry/render_registry.py --check

# Registry cross-checked against the live dispatch_all.c (catches the
# exact class of drift that used to go unnoticed)?
python3 registry/migrate_registry.py --check

# ROM present with the expected hash? (JP 1.1, the version this project
# targets; upstream/vanilla/README.md lists the 3 other accepted CRC32s)
python3 -c "
import zlib
data = open('ff4-port/upstream/rom/ff4-jp1.sfc','rb').read()
crc = format(zlib.crc32(data) & 0xFFFFFFFF, '08X')
print('CRC32:', crc, '(expect CAA15E97 for JP 1.1)')
"

# Translator pitfalls prompts in sync with their single source of truth?
# (reverser_system.md and reverser_hardcore.md forked silently once already —
# P13-P17 landed in one and not the other, cf. W1-5)
python3 ff4-port/prompts/generate_pitfalls.py --check
```

If any of these fail: **stop and diagnose before doing anything else** —
per `workflows/ESCALATION.md` trigger T6, a broken path or missing asset is
an infra problem, not something to route around with a manual workaround.
The W0-1 postmortem (stale absolute paths after the submodule move) is the
concrete example of what NOT diagnosing this first led to.

## 2 — What to work on next

```sh
python3 registry/next_task.py
```

Prints buckets in priority order (`dp_verify`, `no_contract`, `fixable_l1`,
`custom_spike`, `l3_candidate`, `flagged_l2`) — see the script's own
docstring for what each means. Pick from the top of the highest-priority
non-empty bucket unless the user has already named a specific dispatch ID.

## 3 — MemPalace resume sweep (per AGENTS.md §B.4)

1. `mempalace_status` — enumerate wings, exclude `transcripts*`.
2. `mempalace_search(query="[TASK:ongoing]", wing="ff4-gnw", room="task-handoff")`
   — the canonical cross-tool resume lane. Apply the `visible_to` filter
   client-side.
3. If a `[TASK:ongoing]` drawer exists for the work you're about to touch,
   write a `[TASK:checkpoint]` via `mempalace_update_drawer` **before**
   starting — mandatory, not optional (AGENTS.md §B.4 step 6).

## 4 — Before touching a specific dispatch

Read `ff4-gnw/CONVENTIONS.md` for the DP/DB entry-state facts before
trusting a CONTRACT's `dp=`/`db=` fields — they have been wrong for
several confirmed routines, and the corrections/reversals are recorded
there. Check `workflows/ESCALATION.md` for the objective triggers that
mean "stop and hand off" rather than pushing through.

## What this skill does NOT do

- It does not run the desktop build or the oracle — those need the ROM and
  fixtures, and take real time; run them only when actually validating a
  routine (`workflows/WF-DECOMP.md` / `WF-VALID.md`).
- It does not touch git state, dispatch_all.c, or the registry — purely
  read-only orientation.
