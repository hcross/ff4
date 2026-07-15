# WF-DECOMP — Routine decompilation & runtime equivalence

> Turn a 65816 ASM routine into equivalent native C, **proven by per-routine
> runtime equivalence** (the *spike* harness: C vs interpreted-asm from an
> identical entry state). Produces a dispatch at level **L2**. Prerequisite for
> the [WF-VALID](WF-VALID.md) workflow (which pushes it to L3 via in-game validation).
>
> ⚠ The proof is **not** a bit-exact recompilation of the C back into ca65
> asm — abandoned path (cc65 targets the 6502, not the 65816; never byte-equal
> with hand-written asm). The proof is *runtime*, as in zelda3/snesrev.

**Main skill**: `snes-re:asm-to-c-port` (+ `snes-re:snes-asm`,
`snes-re:disasm-trace`). **Agent**: `snes-reverse-engineer`.
**Tools**: `ca65-bridge` (asm extraction/classification), `translator/`
(LLM asm→C translation), `parity/` (`generate_spike.py`, `ff4-spike-*`,
`ff4-parity-compare`).

---

## Input

- A target SNES address (e.g. `$03:9E85`) → ID `D039E85`.
- The reference disassembly: `ff4-port/upstream/notes/ff4j-sfc.asm`.
- The ROM (byte ground truth): `ff4-port/upstream/rom/ff4-jp1.sfc`.

## Output

- A ported C file: first `port/<module>/<func>.c` (translation staging area),
  then promoted to `ff4-gnw/<domain>/<Name>.c` once the spike is green.
- A passing runtime-equivalence spike (`parity/src/spike__<addr>_*.c`).
- An up-to-date entry in [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 1.

---

## Steps

### 0. Context recovery
Apply the **post-compaction protocol** (AGENTS §B.4). Open/update a
`[TASK:ongoing] wf-decomp-D<id>` in MemPalace `wing=ff4-gnw, room=task-handoff`.
Run a **sequential-thinking** sequence dedicated to this routine.

### 1. Resolve the direct page (step zero of EVERY routine)
Determine `D / m / x / DB` at entry. Every `$nn` is `[D + nn]`, not `$00nn`.
Identify the callers to know `D` (FF4 field/NMI: `D=$0600`).
**Record** `D/m/x/DB` as a header comment in the future C file.

### 2. Read the ASM and the ROM bytes
Read the routine in `ff4j-sfc.asm`. Verify every `jsr/jsl/jmp` target
**against the ROM bytes**, not the disassembly labels. Follow the m/x
flags (REP/SEP) to size immediates and opcode lengths.

### 3. Produce the C (manual or LLM-assisted)
Two paths, same output contract (`port/<module>/<func>.c`):
- **Manual**: port by hand, using `sequential-thinking` for the reasoning.
- **Assisted**: `translator/batch_translate.py` (pluggable LLM provider:
  claude-cli / anthropic-sdk / openai-compat) translates asm → C, after
  translate/delegate classification by `ca65-bridge classify`. Always start
  with `--dry-run`, cap with `--budget-usd`.

Porting rules (identical for both paths):
- One C function per ASM routine; **original ROM address as a comment**.
- Variables at their **original WRAM addresses** (`snes->ram[...]`).
- Irreducible control flow → transcribe as `goto`+labels **faithfully
  first**, refactor afterwards.
- Local ROM tables → `static const` at the top of the file.
- `adc/sbc` → `+/-`; an observed incoming carry/garbage is an original bug to
  handle explicitly (ROM patch on the harness side), not to silently replicate.
- **Sync the CPU registers before any `run_emulated_func`**: if the ASM
  does `LDA $xx` before a `JSR`, set `cpu->a` before the call (the cause of the F12 bug).

### 4. Per-routine runtime equivalence — the spike *(EXISTING infra)*
> **Methodology note (ADR to be recorded).** The original target — "recompile
> the C to c65 asm and compare bit-for-bit against the ROM" — is **abandoned**:
> it is unreachable by construction (cc65 targets the 6502, not the 65816, and
> never reproduces FF4's hand-written asm). The **real** proof of equivalence
> is *runtime*, exactly as in zelda3/snesrev — and it's already tooled.

Generate and run the routine's spike:
```sh
python3 translator/generate_spike.py port/<module>/<func>.c   # → parity/src/spike__<addr>_*.c
cd parity && make ff4-spike-<name> && ./ff4-spike-<name> ../upstream/rom/ff4-jp1.sfc [frames]
```
The spike inlines the ported C and compares it, **from an identical entry
state**, against `run_emulated_func` (the original asm executed in the
interpreter): same WRAM/register entry state → run C *vs* asm → compare the
exit state. Green ⇒ the routine's runtime equivalence is proven. `ca65`
(cc65 suite, installed) is used by the `upstream` submodule to
**reassemble the disassembly into the reference vanilla ROM** (the "golden"
ROM for `parity_compare`), not to recompile the C.

> ⚠ **The spike target address comes from the port file's NAME, not from the
> `REVERSED_FUNCTION` line.** `generate_spike.py` resolves the target from
> the file stem via `ca65-bridge` and, on disagreement, trusts the bridge
> ("Trusting the bridge" warning). On a routine whose disassembly annotation
> is offset from its true entry (the recurring off-by-2 class, e.g.
> `D009F6E`), the bridge therefore returns the annotated **wrong** address
> and the spike fails en masse (~4975/5000, asm side executing
> mid-instruction garbage). Workaround: name the port file so the bridge
> cannot resolve it (e.g. `UpdateLocalTilesEntry.c` — falls back to the
> `REVERSED_FUNCTION` address) and add a one-line spike-only `void <stem>_c`
> shim. Evidence: `ff4-port/translator/runs/D009F6E_updatelocaltiles_spike.txt`.

### 5. Boundary coverage *(to be formalised on top of the spikes)*
The spike covers the state reached by the test savestate(s). For **edge
cases** (0, max values, incoming carry, overflows, extreme indices)
that these states may not exercise: extend the spike harness to
inject synthetic entry states before the call and compare the C vs
interpreter outputs. This is an **extension** of the existing spike infra
(`generate_spike.py`), not a separate ASM chain. Tracked in [BACKLOG.md](../BACKLOG.md).

### 6. Log in the registry
Do **not** hand-edit [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) —
Table 1 is generated from [`registry/dispatch_state.jsonl`](../registry/dispatch_state.jsonl).
```sh
python3 registry/registry_promote.py D<id> --to L1 --note "C body written, unvalidated"
# once the spike passes:
python3 registry/registry_promote.py D<id> --to L2 \
    --evidence parity/<spike-run-output-or-log> --note "fuzzed spike, N/N pass"
```
This validates the level transition (won't let you skip L1) and
re-renders DISPATCH_REGISTRY.md automatically.

**If the dispatch table gained a NEW hook** (first-time dispatch, not a
level promotion): regenerate the per-routine ranges and the variant
profiles, then review the routine's variant status — a hook unknown to
`ff4-gnw/rom_profiles.c` runs **ungated** under every patched variant,
which is wrong the moment a patch touches its asm (ADR-008,
ff4-port/docs/adr):

```sh
python3 registry/gen_ranges.py          # new entry needs a proven range
python3 registry/patch_impact.py        # regenerates rom_profiles.c + VARIANT_GAPS.md
                                        # (variant images: apply_ips.py --patch-id <id>)
```

Then read the routine's row in [registry/VARIANT_GAPS.md](../registry/VARIANT_GAPS.md):
`fail-closed` means its range could not be proven (typical for code in
data-modeled banks, see registry/RANGES.md) — the native win does NOT
extend to variants until the range is pinned. The `--check` modes of both
tools guard against forgetting this step (ff4-status runs them).

### 7. Closure
Update the `[TASK:*]` (→ `checkpoint` if continuing, `done` otherwise).
Record any non-trivial discovery as an ADR (`room=architecture-decisions`)
or obstacle (`room=obstacles-and-solutions`). Write a diary entry.

---

## Guardrails

- **Direct page first** (§1) — FF4's #1 cause of bugs.
- **ROM bytes = truth** (§2).
- **Sync CPU registers before `run_emulated_func`** (§3, the F12 lesson).
- **Proof = runtime equivalence (spike), not bit-exact recompilation** (§4).
- A routine is **never** L3 here — that's [WF-VALID](WF-VALID.md)'s job.
- Don't port more than one routine at a time without making it verifiable.
