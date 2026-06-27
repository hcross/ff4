# WF-RELEASE — Game & Watch build & test

> Build the G&W image, flash it, and qualify the deliverable on three axes
> (speed, fidelity, crash-free) with **minimal** human involvement.
> Pushes embedded dispatches to **L4**.

**Skills**: `gnw-hardware:provision` (build/flash/recovery),
`gnw-hardware:debug` (oracle liveness, fault decode, framebuffer dump).
**Hardware-in-the-loop**: probe connection, power on/off, and LCD reading = human.

---

## Input

- An `ff4-gnw` commit (dispatch-table state to embed).
- An ST-Link SWD probe connected, G&W unit powered on.

## Output

- A row in [DISPATCH_REGISTRY.md](../DISPATCH_REGISTRY.md) Table 3:
  date, commit, embedded dispatches, speed, fidelity, crash-free.
- Promotion of dispatches tested without regression to **L4**.

---

## Steps

### 0. Context recovery
Post-compaction protocol (AGENTS §B.4). `[TASK:ongoing] wf-release-<commit>`.

### 1. Probe & device health (human for the wiring)
```sh
bash scripts/health-check.sh        # (gnw-hardware:provision) USB probe + gnwmanager info
```
If "Unable to autodetect probe": check the data cable (not charge-only), USB
enumeration, device powered on. `Filesystem MISSING/CORRUPT` = often a red herring
(gnwmanager's FS, not retro-go's LittleFS).

### 2. Provision the ROM if needed
The ROM is loaded at runtime from FrogFS (`/roms/homebrew/ff4.sfc`).
**`make clean` destroys the gitignored ROM** → copy it back from a copy
outside `sd_content/` (e.g. `ff4-port/upstream/rom/`). Verify the **same SHA-1**
as the RE target, otherwise the C dispatch desyncs.

### 3. Build (canonical flags)
```sh
make INTFLASH_BANK=2 FF4_AUTOBOOT=1 SD_CARD=0 EXTFLASH_SIZE_MB=4 \
     CHECK_DIRTY_SUBMODULE=0 -j4 all
```
- `INTFLASH_BANK=2` — app at `0x08100000` (bootloader bank 1 at `0x08000000`).
- `SD_CARD=0` — assets in internal flash. **`SD_CARD=1` makes `flash` a silent
  no-op.**
- `make clean` is mandatory if `SD_CARD` or another fundamental flag changes
  (but re-provision the ROM afterwards, §2).

### 4. Flash
```sh
make INTFLASH_BANK=2 FF4_AUTOBOOT=1 SD_CARD=0 EXTFLASH_SIZE_MB=4 \
     CHECK_DIRTY_SUBMODULE=0 flash
```
The recipe ends with `start 0x08100000` (direct jump to the app) + `disable-debug`.
Consequences:
- The **real boot test = a power-cycle** (goes through the bootloader); `start`
  alone only validates the app in isolation.
- After `disable-debug`, the probe may need a power-cycle to respond again.

### 5. Qualify — **crash-free** axis (oracle liveness, automated)
```sh
bash scripts/gdbserver-up.sh
arm-none-eabi-gdb -q -nx -batch -x scripts/frames-oracle.gdb build/gw_retro_go.elf
```
- `frames` **advancing** = the emulator is alive.
- `frames == 0` + stable PC = spin; + climbing PC + corrupted backtrace =
  runaway (often a clobbered bootloader → `provision §4` recovery).
- Decode SCB: `VECTACTIVE==0` + `CFSR==0` + `HFSR==0` = no HardFault.

### 6. Qualify — **fidelity** axis (pixel-diff screenshots)
Dump the device framebuffer (gnw-hardware:debug) on key scenes (title, field,
combat) and **pixel-diff** vs a known desktop reference. A black screen with SCB at
0 is **not** a fault — it's a rendering/title problem, not a boot one.

### 7. Qualify — **speed** axis
Measure: dispatch rate (%), effective frames/s, time spent in WaitVblank.
Cross-reference with the desktop (`proof_cyc`, headless dispatch rate) to spot
a perf regression introduced by a dispatch.

### 8. Log (Table 3)
`date | commit | embedded dispatches (IDs) | speed | fidelity | crash-free | notes`.
List the `D<…>` IDs embedded (from `dispatch_all.c` at that commit). Promote
to **L4** the dispatches confirmed without regression on device.

### 9. Closure
Update the `[TASK:*]`, ADR/obstacles, diary. If recovery is needed
(bricked unit), follow `gnw-hardware:provision §4` then re-test.

---

## Guardrails

- `SD_CARD=1` → `flash` silently does **nothing**. Use `SD_CARD=0`.
- `make clean` erases the gitignored ROM → re-provision (§2).
- Verify the **ROM SHA-1** matches the RE target.
- Power-cycle = the real boot test; `disable-debug` can block the probe
  until the power-cycle.
- **Fidelity by screenshot**, never by liveness alone (corrupted rendering
  passes the frame oracle).
- Automate as much as possible (GDB batch); reserve human involvement for
  wiring / power / LCD reading.
