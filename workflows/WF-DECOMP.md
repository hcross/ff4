# WF-DECOMP — Routine decompilation & formal validation

> Turn a 65816 ASM routine into equivalent native C, **proven** by
> bit-exact recompilation and boundary unit tests. Produces a dispatch at
> level **L2**. Prerequisite for the [WF-VALID](WF-VALID.md) workflow (which
> pushes it to L3).

**Main skill**: `snes-re:asm-to-c-port` (+ `snes-re:snes-asm`,
`snes-re:disasm-trace`). **Agent**: `snes-reverse-engineer`.

---

## Input

- A target SNES address (e.g. `$03:9E85`) → ID `D039E85`.
- The reference disassembly: `ff4-port/upstream/notes/ff4j-sfc.asm`.
- The ROM (byte ground truth): `ff4-port/upstream/rom/ff4-jp1.sfc`.

## Output

- A ported C file `ff4-gnw/<domain>/<Name>.c`.
- An up-to-date entry in [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 1.
- *(once the infra exists)* a C unit test + its c65 ASM equivalent.

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

### 3. Produce the C (sequential-thinking for the reasoning)
- One C function per ASM routine; **original ROM address as a comment**.
- Variables at their **original WRAM addresses** (`snes->ram[...]`).
- Irreducible control flow → transcribe as `goto`+labels **faithfully
  first**, refactor afterwards.
- Local ROM tables → `static const` at the top of the file.
- `adc/sbc` → `+/-`; an observed incoming carry/garbage is an original bug to
  handle explicitly (ROM patch on the harness side), not to silently replicate.
- **Sync the CPU registers before any `run_emulated_func`**: if the ASM
  does `LDA $xx` before a `JSR`, set `cpu->a` before the call (the cause of the F12 bug).

### 4. c65 ASM recompilation + bit-exact comparison ⚠ *(infra to be built)*
> This step is **not yet implemented**. Target:
> 1. Recompile the C routine to 65816 via a c65 toolchain.
> 2. Compare the produced binary **byte for byte** against the original ROM
>    range (or its functional equivalent after address normalisation).
> 3. Any discrepancy = either a porting bug, or a documented original bug
>    (assert-guarded ROM patch on the harness side).
>
> Until it exists, a routine caps at **L1** on the decompilation criterion
> and can only reach L2 through the unit tests (step 5) alone — to be
> marked explicitly in the registry. Tracked in [BACKLOG.md](../BACKLOG.md).

### 5. Boundary unit tests (C + c65 ASM) ⚠ *(infra to be built)*
> Target: for each routine, edge cases (0, max values, incoming carry,
> overflows, extreme indices) executed **in C** and **in c65 ASM**,
> with output comparison (targeted WRAM + registers). Validates boundary
> behaviour that the in-game oracle doesn't necessarily cover.

### 6. Log in the registry
Update [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 1:
`ID | address | routine | domain | level | notes`. Level reached:
- **L1** if only the C body is written;
- **L2** if C+ASM unit tests pass (and ideally bit-exact recompilation is OK).

### 7. Closure
Update the `[TASK:*]` (→ `checkpoint` if continuing, `done` otherwise).
Record any non-trivial discovery as an ADR (`room=architecture-decisions`)
or obstacle (`room=obstacles-and-solutions`). Write a diary entry.

---

## Guardrails

- **Direct page first** (§1) — FF4's #1 cause of bugs.
- **ROM bytes = truth** (§2).
- **Sync CPU registers before `run_emulated_func`** (§3, the F12 lesson).
- A routine is **never** L3 here — that's [WF-VALID](WF-VALID.md)'s job.
- Don't port more than one routine at a time without making it verifiable.
