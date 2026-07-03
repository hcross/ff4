# ESCALATION — when a Sonnet-class agent must hand off

> A decision **table**, not prose. Every trigger below is evaluated on a
> tool's exit code, a registry flag, or a machine-readable field — never on
> "this feels hard." A Sonnet-class agent hitting any T-code stops the
> current attempt immediately, records the escalation, and does not
> improvise a workaround. This generalizes a pattern already proven at the
> translation-stage level: `translator/cascade_translate.py`'s
> `TERMINAL_NO_ESCALATE` set (pass/delegate_pass/custom_spike/spike_timeout/...)
> already stops its cascade at the first stage that reaches one of those
> statuses and escalates everything else to the next model tier. The table
> below extends the same discipline to the whole WF-DECOMP/WF-VALID loop,
> not just translation.

## Triggers

| Code | Condition (mechanically checked) | Action |
|------|-----------------------------------|--------|
| **T1** | `generate_spike.py` reports `fails > 0` after exactly one re-translation retry | Escalate: `divergence` — the retry budget is spent, a human/frontier session must read the fuzzed failing trial and the asm side by side |
| **T2** | `generate_spike.py` exits 3 (`CONTRACT_MMIO_MISMATCH`) | Escalate: `contract-mmio` — declaring `mmio_effects`/`dma` correctly requires reading the asm's DB/bus semantics; do not guess an address list to make the check pass |
| **T3** | `generate_spike.py` reports `CUSTOM_SPIKE` (indexed store, no single-slot contract) | Escalate: `harness-design` — designing a `SPIKE_COMPARE: region`/`SPIKE_MASK` needs judgment about which WRAM ranges are legitimately unobserved dead scratch vs. a real omission |
| **T4** | An oracle divergence (`oracle_ab.c --json`, `verdict: "divergence"`) does not match a known artifact class (byte-exact `wram_first_offsets` empty while the CRC differs = cycle-skew false positive; `native_hang` with no prior divergence = a genuine stall, not a functional bug to diagnose the same way) | Escalate: `oracle-divergence` — root-causing under timing noise is exactly the class of work that produced phantom culprits (Mult8/Mult16, `14FD03`) in this project's own history |
| **T5** | `registry/classify_flags.py` set `WAIT_BLOCKING`, `TAIL_JML`, or `SPC_MAILBOX` on the candidate routine | **Terminal, no escalation**: do-not-dispatch. These are categorical exclusions (the `ExecBtlGfx`/`ExecCmd` classes), not judgment calls — record the routine as `RETIRED`/excluded via `registry_promote.py` with the flag as the reason, do not attempt a workaround (delegating a `WAIT_BLOCKING` routine to `run_emulated_func` reproduces the exact ExecBtlGfx hang: synchronous single-frame execution can't service a multi-frame wait) |
| **T6** | Any tool exits with `FileNotFoundError`, a path-resolution error, or an unexpected non-zero exit not covered above | Escalate: `infra` — a relocated repo, a stale hardcoded path (the exact W0-1 class of bug), or a broken assumption about the checkout layout. **Never** improvise a manual copy, a wrong-directory commit, or a bypassed check to route around it; diagnosing infra drift is exactly the class of mistake a weaker model makes under pressure (see the W0-1 postmortem: a real regeneration attempt destroyed 186 lines before being caught) |

## What "escalate" means in practice

Record the escalation where the current work is tracked (a MemPalace
`[TASK:*]` drawer, or the calling script's own JSONL log) with:
`handoff_key`, the trigger code (T1-T6), the dispatch ID if applicable, and
every artifact needed to resume without re-deriving context (spike output,
oracle `--json`, the exact command that failed). Do not delete or revert
work already done up to the escalation point — a partial, well-documented
attempt is more useful to whoever picks it up than a clean slate.

## What does NOT require escalation

- A spike passing cleanly (`fails == 0`) — promote via `registry_promote.py`
  and move to the next candidate.
- A `CONTRACT_MMIO_MISMATCH` the agent can fix by correctly reading the
  asm's already-resolved hardware symbols (via `ca65-bridge get-asm`) and
  declaring them — this is mechanical once the addresses are known; only
  escalate if the DB at that point in the routine is itself ambiguous.
- A `DP_SENSITIVE` flag on a routine in a module with an established D
  value (`battle`) — the flag exists for `field`/`menu`, where the true D
  is unverified per routine (see `ff4-gnw/CONVENTIONS.md`); verifying one
  routine's actual entry D via a runtime trace (`printf snes->cpu->dp`,
  the method that confirmed `CheckMenu_c`) is exactly the kind of scoped,
  mechanical task Sonnet-class models have executed successfully in this
  project once a frontier session established the method.

## Provenance

The T1-T6 shape is not aspirational — every trigger corresponds to a
documented failure mode already observed in this project:
- T1/T4: the ATB bug investigation (MemPalace `wing=ff4-gnw`, exploration
  tree 2026-06-25) initially suspected `Mult8_btlgfx`/math-util routines
  from oracle divergence signals; the 2026-06-30 SDL bisection cleared
  them ("Mult8/Mult16 spike PASS, hors de cause pour la logique") and
  found the ATB `--no-charge` frame-4 divergence was itself "bruit timing
  inoffensif" — a session's worth of chasing a phantom culprit that a
  cycle-skew classification would have short-circuited immediately.
- T2: the `InitMapRAM_c`/`TfrBGGfx_c` false-L2 incidents
  (`DISPATCH_REGISTRY.md`) and the `ExecInterrupt_c` demotion (this
  session) — a spike passing does not mean a CONTRACT correctly declares
  MMIO effects.
- T5: the `ExecBtlGfx` root-cause investigation (2026-06-30, "validated
  SDL par Hoani") — a multi-day investigation to establish exactly the
  category rule T5 now encodes as a static, pre-flight check.
- T6: the stale absolute-path bugs found and fixed in Wave 0
  (`gen_dispatch.py`, `port_validated.py`, `volume_iterate.py`) and the
  confirmed-destructive `gen_dispatch.py` regeneration attempt.
