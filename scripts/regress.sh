#!/usr/bin/env bash
# regress.sh — local regression runner over every fixture.
#
# NOT a "0 divergence expected" check: several fixtures (006-in-combat, at
# least) have KNOWN, documented, not-yet-fixed divergences (the btlgfx
# cluster, see BACKLOG.md). Treating any divergence as failure would make
# this script cry wolf every single run. Instead: record each fixture's
# oracle verdict, and on every subsequent run, flag a fixture whose verdict
# CHANGED since last time — that is the actual definition of a regression.
# First run on a machine just establishes the baseline (no verdict yet to
# compare against).
#
# Baselines live in .regress-baselines/ (gitignored, local-only, like the
# ROM and fixtures themselves) — they are this-machine, this-ROM-copy
# state, not portable, and licensed-asset-adjacent by construction.
#
# Usage: scripts/regress.sh [--frames N] [--reset] [--fixtures NAME,NAME,...]
#   --reset      forget all recorded baselines and start fresh this run
#   --fixtures   comma-separated fixture basenames (no .lss), e.g.
#                --fixtures 001-scene-after-leaving,004-menu — scope to a
#                fast subset. The combat-adjacent fixtures (002, 005, 006)
#                are markedly slower: AGENTS.md documents the interpreter
#                running ~6x slower than native per headless frame, and
#                these seeds exercise more of it; a full run across all 11
#                fixtures at a meaningful frame count is a multi-minute
#                affair, not a quick check — scope down while iterating.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UMBRELLA="$(cd "$HERE/.." && pwd)"
DESKTOP="$UMBRELLA/ff4-port/desktop"
ROM="$UMBRELLA/ff4-port/upstream/rom/ff4-jp1.sfc"
BASELINE_DIR="$UMBRELLA/.regress-baselines"
FRAMES=300
RESET=0
FIXTURES_FILTER=""

while [ $# -gt 0 ]; do
  case "$1" in
    --frames) FRAMES="$2"; shift 2 ;;
    --reset) RESET=1; shift ;;
    --fixtures) FIXTURES_FILTER="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Baseline exclusion set (F3/F4/F6/F-NEW: intentional DMA-bypass/stub
# routines) — same as desktop/Makefile's oracle-baseline target. Single-
# source concern flagged but not fixed here (see next_task.py's own
# backlog); kept in sync by hand for now.
EXCLUDE="--exclude 15cadc --exclude 048004 --exclude 03fe03 --exclude 15ca5e"

mkdir -p "$BASELINE_DIR"
if [ "$RESET" -eq 1 ]; then
  rm -f "$BASELINE_DIR"/*.verdict
fi

echo "=== regress.sh: building headless-all (no SDL required) ==="
make -C "$DESKTOP" headless-all

if [ ! -f "$ROM" ]; then
  echo "error: ROM not found at $ROM" >&2
  echo "       see ff4-port/vanilla/README.md for the accepted CRC32 values" >&2
  exit 2
fi

shopt -s nullglob
if [ -n "$FIXTURES_FILTER" ]; then
  fixtures=()
  IFS=',' read -ra names <<< "$FIXTURES_FILTER"
  for n in "${names[@]}"; do
    f="$UMBRELLA/ff4-port/$n.lss"
    if [ ! -f "$f" ]; then
      echo "error: fixture not found: $f" >&2
      exit 2
    fi
    fixtures+=("$f")
  done
else
  fixtures=("$UMBRELLA"/ff4-port/*.lss)
fi
if [ ${#fixtures[@]} -eq 0 ]; then
  echo "error: no .lss fixtures found under $UMBRELLA/ff4-port/ — see FIXTURES.md" >&2
  exit 2
fi

REGRESSED=0
for lss in "${fixtures[@]}"; do
  name="$(basename "$lss" .lss)"
  json_out="/tmp/regress_${name}.json"
  log_out="/tmp/regress_${name}.log"

  "$DESKTOP/ff4-desktop-oracle" "$ROM" --load "$lss" --frames "$FRAMES" $EXCLUDE \
      --json "$json_out" > "$log_out" 2>&1 || true

  verdict="$(python3 -c "
import json
try:
    print(json.load(open('$json_out'))['verdict'])
except Exception:
    print('unknown')
" 2>/dev/null)"

  baseline_file="$BASELINE_DIR/${name}.verdict"
  prev="$(cat "$baseline_file" 2>/dev/null || true)"

  if [ -z "$prev" ]; then
    echo "$name: $verdict (first run on this machine — baseline recorded)"
  elif [ "$prev" = "$verdict" ]; then
    echo "$name: $verdict (unchanged)"
  else
    echo "$name: REGRESSION — was '$prev', now '$verdict'"
    echo "         details: $json_out / $log_out"
    REGRESSED=1
  fi
  echo "$verdict" > "$baseline_file"
done

echo
if [ "$REGRESSED" -ne 0 ]; then
  echo "regress.sh: REGRESSION DETECTED — see above"
  exit 1
fi
echo "regress.sh: no verdict changes since the last recorded run"
