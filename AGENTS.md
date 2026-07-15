# FF4 → Game & Watch — Project context

> Launch point for the CLI tool that ports **Final Fantasy IV**
> (Super Famicom, NTSC-J) to the **Nintendo Game & Watch** (STM32H7B0).
> This file carries the **stable** context valid for both sub-projects,
> survives compactions, and points to the **living** tracking documents.

---

## Language policy — English only, everywhere, no exceptions

**Every artifact produced for this project MUST be in English**, regardless
of any global or session-level language preference the assisting agent might
otherwise follow (e.g. a `~/.claude/rules/*.md` "respond in French"
directive). That preference governs conversation with the user — it never
governs what gets written into these repositories. This project instruction
**overrides** it, per Claude Code's own precedence rules for project-level
`AGENTS.md`/`CLAUDE.md` files.

Covers, without exception, across `ff4`, `ff4-gnw`, and `ff4-port`:

- **File content** — code, comments, docstrings, commit-tracked
  Markdown/docs, generated artifacts kept under version control (spikes, logs).
- **Git commit messages** — subject and body.
- **GitHub assets** — issue titles/bodies/comments, PR titles/descriptions/
  reviews, release notes, GitHub Actions workflow names, repository
  description and topics.

> ⚠ **This has already broken twice.** `ff4-port` commit `e370941` (2026-06)
> documents an LLM translation run that picked up the user's global French
> CLI preference and emitted French inline comments in generated C — caught
> only after the fact. The entire `translate/en` history rewrite (2026-07,
> all three repos, `archive/untranslated-main` holds the pre-rewrite state)
> exists because French had crept back into commits and docs since. Do not
> repeat either failure mode: **check the language of what you are about to
> write to this repo before writing it, independent of what language you are
> conversing in.** If in doubt, write in English.

---

## A — Static context

### A.1 The two projects

The effort is split across two repositories, mounted as **git submodules** of
this umbrella directory (`ff4/`).

| Project | Role | Key contents |
|--------|------|-------------|
| **`ff4-gnw/`** | C sources of the port — the artifact that runs on the device | Dispatch table (`dispatch_all.c`/`.h`), ported routines (`battle/`, `field/`, `menu/`, `cutscene/`, `sound/`), LakeSnes helpers (`ff4_helpers.c`), LakeSnes fork (`snes/`), G&W glue (`main.c`) |
| **`ff4-port/`** | Validation infrastructure — the oracle and ground truth | Reference disassembly (`upstream/notes/ff4j-sfc.asm`), ROM (`upstream/rom/ff4-jp1.sfc`), desktop harness (`desktop/`), reference savestates (`fixtures/*.lss`, private submodule — see [FIXTURES.md](https://github.com/hcross/ff4-port/blob/main/FIXTURES.md)), `desktop/KNOWN_FINDINGS.md` |

`ff4-gnw` compiles **twice** from the same C sources:
- for the **device** (STM32H7B0, via the retro-go-sd build);
- for the **headless desktop** (validation), via `ff4-port/desktop/Makefile` which
  links the live `ff4-gnw` tree (`FF4GNW ?= ../../ff4-gnw`).

### A.2 Overall intent

Port FF4 to the Game & Watch by **progressively replacing** interpreted SNES
routines with *dispatched* native C. LakeSnes (65816 interpreter) serves both
as the embedded execution engine and as the **ground-truth reference**: every
ported routine must be proven equivalent to the original before it can be trusted.

The central mechanism is the **dispatch**: `ff4_dispatch_try()` (in
`dispatch_all.c`) intercepts `JSR`/`JSL` (opcodes `0x20`/`0x22`) to a known
SNES address and runs the matching C routine instead of
interpreting it. The `JML` (`0xDC`) is **not intercepted** — hence some
tail-jump-ending routines that must stay in the interpreter.

> ⚠ **Known dispatch limits** (keep these in mind at all times):
> - The WRAM write-hook (`snes_wram_write_hook`) is **blind to direct C
>   writes** (`snes->ram[x] = v`). Tracing a dispatched routine goes through
>   `--trace-frame` or an embedded `printf`, not a WRAM watchpoint.
> - The pure interpreter is **~6× slower in headless frames** on the
>   `WaitVblank` path: the anti-hang guard of `snes_runFrameBounded` (50M opcodes/
>   frame) forces the exit. **Compare at equal SNES `frames_run`**, never at
>   equal headless frame count.
> - `ff4_dispatch_try` does not charge the cycle cost of the original routine
>   → slight PPU timing skew between the native pass and the interpreted pass.

### A.3 Topology & submodule prerequisites

```
ff4/                          ← umbrella repo (CLI launch point)
├── CLAUDE.md                 ← @AGENTS.md
├── AGENTS.md                 ← this file (stable context)
├── DISPATCH_REGISTRY.md      ← living registry of dispatches (IDs, maturity)
├── BACKLOG.md                ← existing → target realignment work
├── REPRISE.md                ← selective asset reset (requalification)
├── workflows/
│   ├── WF-DECOMP.md          ← decompilation + formal validation of a routine
│   ├── WF-VALID.md           ← in-game behavioral validation (oracle + GDB)
│   └── WF-RELEASE.md         ← build + G&W test, release table
├── ff4-gnw/   (submodule)
└── ff4-port/  (submodule)
```

**Prerequisite before freezing the submodules**: a git submodule references a
**pushed commit** on the remote. Local commits in `ff4-gnw` / `ff4-port`
must be pushed (e.g. Gitea "Odan") before the umbrella pins them.
As long as the submodule setup is not done, this directory hosts
only the documentation and the two projects remain at their current
location. Tracked in [BACKLOG.md](BACKLOG.md).

### A.4 Available tools

#### Claude Code plugins (local marketplace)

| Plugin / Skill | Usage |
|----------------|-------|
| **`snes-re`** (agent `snes-reverse-engineer`) | 65816 analysis, reverse-engineering, asm→C porting. **Analysis only** — handoff to `gnw-hardware` for the device. |
| `snes-re:snes-asm` | 65816 reference + mental model; recurring pitfalls inline, heavy hardware reference in MemPalace `wing=snesdev`. |
| `snes-re:asm-to-c-port` | **Porting procedure** side-by-side-compare (zelda3/smw methodology): `g_ram` overlay at original addresses, per-frame harness comparison, `run_emulated_func` bridge, ROM patch for original bugs, validation by screenshot. |
| `snes-re:disasm-trace` | Disassembly tooling: code/data tracing with m/x flag tracking, LoROM/HiROM mapping, cross-checking against a reference. |
| **`gnw-hardware:provision`** | Build + flash + device recovery (gnwmanager, openocd, ST-Link SWD). **Hardware-in-the-loop**: probe connection / power on / LCD reading = human. |
| **`gnw-hardware:debug`** | On-device diagnosis via `gnwmanager gdbserver` + `arm-none-eabi-gdb`: Cortex-M fault decoding (SCB/CFSR/HFSR), vector-table integrity, **frame liveness oracle**, runaway/spin/clean-return classification. |

> **`snes-re` golden rules** (causes of historical FF4 bugs):
> 1. **The direct-page register (D) is pitfall no. 1.** Any `$nn` operand is
>    `[D + nn]` (bank `$00`), NOT `$00nn`. The NMI/FieldMain-loop context runs
>    `D=$0600`, `menu` runs `D=$0100` — but this is **not uniform per module**;
>    see [`ff4-gnw/CONVENTIONS.md`](ff4-gnw/CONVENTIONS.md) for the
>    per-routine evidence before assuming either value, and
>    `registry/classify_flags.py`'s `DP_SENSITIVE` flag for a mechanically
>    surfaced (not confirmed) "verify this" list.
> 2. **The ROM bytes are the truth**, not the disassembly annotations.
> 3. **Track the m/x flags** (REP/SEP) to size immediates and opcodes.
> 4. **Validate every rendering increment by screenshot** (pixel-diff), never
>    by fps/frame counter/fault register alone.

#### Desktop harness (`ff4-port/desktop/`)

Links the live `ff4-gnw` tree. Compiled under the **same contract** as the device
(`-DFF4_PORT_STATIC_SNES`: static `Snes` singleton, device `pixelBuffer` dims,
`ff4_dispatch_try` hook in `cpu.c`). `make all` produces:

| Binary | Role | Key flags |
|---------|------|-----------|
| `ff4-desktop-headless` | Run N frames, dump frame | `--frames N`, `--load f.lss`, `--out f.ppm`, `--no-dispatch`, `--watch-wram ADDR [--watch-wram-hi HI]`, `--trace-frame N` |
| `ff4-desktop-sdl` | Interactive window | `--load`, `--save-prefix`, `--scale`. Keys: arrows=d-pad, x=A z=B a=Y s=X d=L c=R, RShift=Select, Return=Start, Space=pause, `.`=step, `g`=toggle interpreter (input+sound stay native), `5`=save slot, `9`=reload, `0`=screenshot |
| `ff4-desktop-oracle` (`oracle_ab.c`) | A/B comparison dispatch vs interpreter, frame by frame; calibration pass + **cycle charging** (hardening) | `--load SEED`, `--frames N`, `--exclude HEX` (repeatable), `--no-charge` |
| `wram_diff` | Byte-exact WRAM diff between two passes | masks the stack region |
| `proof_cyc` | Cycle analysis + PC progression per frame | |
| `miss_profiler` | Tally of missed PCs → list of hot routines to port | |

Useful `make` targets: `make oracle SEED=…`, `make oracle-baseline SEED=…`
(excludes the intentional DMA-bypass routines: `15cadc 048004 03fe03 15ca5e`).

#### Per-routine decompilation & runtime equivalence (`ff4-port/`)

| Component | Role |
|-----------|------|
| `ca65-bridge/` | Python bridge for **reading** the ca65 disassembly: `get-asm`, `xrefs-from/to`, `search`, `classify` (translate vs delegate, ADR-003). |
| `translator/` | LLM-assisted **asm → C** translation (`batch_translate.py`, pluggable provider claude-cli / anthropic-sdk / openai-compat; `--dry-run`, `--budget-usd`). Output: `port/<module>/<func>.c`. |
| `parity/` | **Runtime** equivalence. `generate_spike.py` → `spike__<addr>_*.c`: ported C vs `run_emulated_func` (interpreted asm) at identical input state → compares the output state (**L2 proof**). `ff4-parity-compare`: two ROMs in lock-step, WRAM/SRAM/VRAM/OAM/CGRAM memcmp per frame. |

> `ca65`/`cl65` (cc65 suite) are installed but serve the `upstream`
> submodule to reassemble the disassembly into a **vanilla reference ROM** — not
> to recompile the ported C. There is **no** bit-for-bit C→ASM comparison (path
> abandoned, cf. §B.2). `port/` is the translation zone; a routine validated
> by its spike is promoted to `ff4-gnw/<domain>/`.

#### Translation-patch variants & ROM identity (ADR-008)

Community translation patches: **one language = one canonical pre-patched
ROM image + one dispatch profile keyed by the image's full-file CRC32**.
Decision record:
[`ff4-port/docs/adr/adr-008-translation-patches-crc-profiles.md`](https://github.com/hcross/ff4-port/blob/main/docs/adr/adr-008-translation-patches-crc-profiles.md).

| Component | Role |
|-----------|------|
| `ff4-port/patches/` | Offline IPS applier (`apply_ips.py`: canonical variant image + modified-range report); `manifest.json` pins hashes, application parameters and per-variant validation status. See [`patches/README.md`](https://github.com/hcross/ff4-port/blob/main/patches/README.md). |
| `registry/gen_ranges.py` | Per-routine byte extents (`dispatch_ranges.json`, proven out-of-band ld65 relink) + frozen-data dependencies (`extra_ranges.json`). Documented in [registry/RANGES.md](registry/RANGES.md). |
| `registry/patch_impact.py` | Byte-diff × ranges × transitive callee closure → **generates** `ff4-gnw/rom_profiles.c` (`--check`-guarded). DELEG wrappers exempt; unresolved entries always-gated (fail-closed). |
| `ff4-gnw/rom_ident.c` + gate array | Full-file CRC32 at `ff4_init` arms the per-slot `ff4_dispatch_gate[]` in `dispatch_all.c`; gated hooks fall through to the interpreter (counted in `ff4_dispatch_gated`, **not** as misses). Unknown CRC: device refuses (`FF4_REQUIRE_KNOWN_ROM`), desktop warns and disables dispatch. |
| `scripts/regress.sh --rom` | Runs the regression suite against another image; baselines keyed per ROM CRC32 (`.regress-baselines/<CRC32>/`). |

Registry L-levels stay scoped to the **vanilla** JP image; per-variant
validity lives in the manifest only. First variant: J2e EN v3.21 (CRC32
`F135CAE6`), device-validated (2026-07-15).

#### LakeSnes specifics (fork in `ff4-gnw/snes/`)

- `snes_runFrameBounded` — anti-hang guard (50M opcodes/frame). Cause of the
  6× interpreter factor (cf. A.2).
- `snes_wram_write_hook` — WRAM watchpoint, **blind to C** (cf. A.2).
- `run_emulated_func(snes, pc)` — runs a SNES address in the interpreter
  from C (incremental one-routine-at-a-time bridge).

### A.5 Reference documentation

- **MemPalace** (persistent cross-tool agent memory):
  - `wing=ff4-gnw`: `room=architecture-decisions` (ADR), `room=obstacles-and-solutions`,
    `room=task-handoff` (resume lane `[TASK:*]`).
  - `wing=snesdev`: 65816/PPU/DMA/APU hardware reference, fed by
    `snes-re` (`room=ref-<source>`, `room=pitfalls`). Queried via
    `mempalace_search(wing="snesdev", room="ref-…", …)`.
- **`ff4-port/desktop/KNOWN_FINDINGS.md`**: findings F1→F12 documented with
  reproduction, root cause, fix and validation. **Source of truth** on the state
  of known bugs; read it before touching a routine already investigated.
- **`ff4-port/FIXTURES.md`**: catalog of reference savestates (`.lss`,
  in the private `fixtures/` submodule — protected assets, never public):
  scene, PC, usage, related findings, and how to (re)generate them if the
  submodule isn't reachable. Consult it to pick a repro/validation fixture.

---

## B — Dynamic context

### B.1 Unique dispatch identifier

Format: **`D<bank><addr>`** — derived mechanically from the SNES address (6 upper-case
hexadecimal digits of the PC `bank:addr`).

```
D0397B3  → $03:97B3  InitAction_c
D0383B9  → $03:83B9  Mult16_c
D03FE03  → $03:FE03  TfrSprites_c
```

Properties: unique, collision-free, stable as long as the routine does not change
address, computable without a central registry. Each dispatch is referenced by
this ID in **all** workflows, the registry, the commits and MemPalace.

### B.2 Maturity scale L0 → L4

**Cumulative** level: a dispatch only moves to `Ln+1` after satisfying `Ln`.

| Level | Meaning | Passing criterion |
|--------|---------------|--------------------|
| **L0** | No-op stub | Present in the table but empty body / `_emu` no-op. To handle or remove. |
| **L1** | Ported, untested | C body written, compiles, but no equivalence proof. |
| **L2** | Per-routine runtime equivalence | The **spike** passes: C vs interpreted-asm at identical input state → same outputs (`parity/`, `generate_spike.py`). Boundary coverage still to formalize. |
| **L3** | Oracle validation | Isolated savestate (only this dispatch active), `wram_diff = 0`, no drift. |
| **L4** | Device-validated | Integrated into the G&W build, tested on device (liveness oracle + screenshot), no crash. |

> **No bit-for-bit C→ASM recompilation**: path abandoned (cc65 targets the
> 6502, never byte-equal with hand-written 65816 asm). The equivalence
> proof is *runtime* (per-routine spike, then in-game oracle), zelda3/snesrev
> method. The spike infra **already exists** (`parity/`, `translator/`).
>
> **Spike audit + promotion (2026-06-27/28, dated snapshot — for the CURRENT
> distribution see [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md), which has
> since moved with individual L2→L3 promotions)**: L0=1 · L1=23 · L2=162 ·
> L3=5 · EXCL=3 · **DELEG=12**. 155 routines credited L2 by
> `batch_spike_ffgnw.py` (fuzzed spike on the `ff4-gnw` bodies). The
> "build_error" catch-all was cleared: 12 delegate→DELEG, 19 run_hang (false
> hangs = compound budget, re-run with reduced budget → L2), 2 parser_error
> (hardened parser → L2), 2 compile_error remaining. The 23 L1: 11 no_source
> (bundled btlgfx), 8 no_contract, 2 fail (`CheckMenu`/`TfrBGAnimGfx`), 2
> compile_error. `DELEG` = wrapper running the asm via `run_emulated_func`.

### B.3 Workflows (summary)

The **detailed and precise** walkthrough of each workflow is in `workflows/`.
Each workflow uses **MemPalace** for long-term tracking and
**sequential-thinking** for multi-turn subtasks.

| Workflow | Goal | Detail |
|----------|-----|--------|
| **WF-DECOMP** | Decompile an ASM → C routine (manual or LLM), prove per-routine **runtime equivalence** via the spike, record it (L2) | [workflows/WF-DECOMP.md](workflows/WF-DECOMP.md) |
| **WF-VALID** | Validate in-game behavior via the oracle (isolated savestate, CRC/screenshot, GDB if needed) | [workflows/WF-VALID.md](workflows/WF-VALID.md) |
| **WF-RELEASE** | Build and test the G&W version, measure quality (speed, fidelity, crash-free) | [workflows/WF-RELEASE.md](workflows/WF-RELEASE.md) |

### B.4 Post-compaction recovery protocol

To run **at session start** and **after any compaction** before
resuming work:

1. **Compute `<project-name>`** = `ff4-gnw` (reference wing of the port).
2. **`mempalace_status`** — enumerate the wings; exclude `transcripts*`.
3. **Handoff lookup**:
   `mempalace_search(query="[TASK:ongoing]", wing="ff4-gnw", room="task-handoff")`.
   Apply the `visible_to` filter client-side.
4. **Read this file** (`AGENTS.md`) for the static context.
5. **Read [DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md)** for the state of the dispatches,
   and [REPRISE.md](REPRISE.md) for the requalification work in progress.
6. **If a `[TASK:ongoing]` exists for `ff4-gnw`**: write **immediately** a
   `[TASK:checkpoint]` via `mempalace_update_drawer` (timestamp, `writer_agent`,
   `resumed_from`, `progress`) **BEFORE** any actual work. Mandatory.
7. **`sequential-thinking`**: reconstruct the ongoing reasoning from the
   drawer, then resume the subtask at the point indicated by `next:`.

At session end: update the `[TASK:*]` drawer, record decisions
(ADR) and obstacles, write a diary entry.

### B.5 Living tracking documents

- **[DISPATCH_REGISTRY.md](DISPATCH_REGISTRY.md)** — registry of the active
  dispatches (row counts and distribution are generated — see the file), 3
  tables (decompilation/tests, game validation, releases). **Table 1 and the
  distribution line are generated** from [`registry/dispatch_state.jsonl`](registry/dispatch_state.jsonl)
  (between the `<!-- REGISTRY:*:START/END -->` markers) — never hand-edit
  either; use `python3 registry/registry_promote.py D<id> --to L<n> --evidence
  <path> --note "..."` to change a level (validates the transition and
  re-renders automatically). `registry/render_registry.py --check` detects
  drift; `registry/migrate_registry.py --check` cross-checks the ID/PC set
  against `ff4-gnw/dispatch_all.c` — stripping C comments first, since
  retired entries live on as tombstone comments that a naive regex
  re-detects (any tool pattern-matching `dispatch_all.c` must do the same).
  `registry/gen_ranges.py --check` / `registry/patch_impact.py --check`
  guard the variant byte-ranges and the generated `ff4-gnw/rom_profiles.c`
  (cf. §A.4 translation-patch variants, ADR-008).
- **[BACKLOG.md](BACKLOG.md)** — existing → target work.
- **[REPRISE.md](REPRISE.md)** — selective reset per layer, requalification order.

---

## Quick start

```sh
# Build the desktop harness (from ff4-port/desktop/)
cd ff4-port/desktop && make all

# Launch a reference battle in a window
make sdl ROM=../upstream/rom/ff4-jp1.sfc        # then load a .lss with 9

# A/B comparison (dispatch vs interpreter) on a savestate
make oracle SEED=../fixtures/006-in-combat.lss FRAMES=600

# Byte-exact WRAM diff at the divergence frame
./wram_diff ../upstream/rom/ff4-jp1.sfc ../fixtures/006-in-combat.lss
```
