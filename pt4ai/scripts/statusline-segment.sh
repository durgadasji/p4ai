#!/usr/bin/env bash
# One short segment for your status line, printed with no newline so it can sit
# beside whatever else you already show there.
#
# This exists because the status line is the only surface that does not scroll.
# Everything else this package says arrives in the transcript and is gone once
# the conversation moves on, which is fine for a notice and wrong for a state.
# Setup being half finished is a state. So is a check that is armed for nothing.
#
# It never replaces your status line. Call it from the one you already have:
#
#     printf "%s" "$(bash ~/.claude/precision/statusline-segment.sh)"
#
# Silent when the precision directory does not exist, so installing this and
# declining to configure anything costs you no pixels.

PRECISION_DIR="${PRECISION_DIR:-$HOME/.claude/precision}"
[ -d "$PRECISION_DIR" ] || exit 0

MARKER="$PRECISION_DIR/setup-in-progress"

# The five files the interview asks about, in its order. Optional ones are
# deliberately not counted: they are declined rather than missing, and a
# denominator that grew every time you skipped something optional would report
# a decision as a deficit.
ASKED="guarded-roots.txt house-style.txt terms.txt working-prefix.txt public-repos.txt"

armed=0
total=0
for f in $ASKED; do
  total=$((total + 1))
  # A file counts as armed only if it holds something other than comments and
  # blank lines, the same test the panel uses. An empty file is not an answer.
  if [ -f "$PRECISION_DIR/$f" ] && grep -qvE '^\s*(#|$)' "$PRECISION_DIR/$f" 2>/dev/null; then
    armed=$((armed + 1))
  fi
done

if [ -f "$MARKER" ]; then
  q=$(grep '^question:' "$MARKER" 2>/dev/null | head -1 | tr -dc '0-9')
  printf "pt4ai: setup %s/%s" "${q:-?}" "$total"
elif [ "$armed" -eq "$total" ]; then
  printf "pt4ai: armed"
elif [ "$armed" -eq 0 ]; then
  printf "pt4ai: unconfigured"
else
  printf "pt4ai: %s/%s" "$armed" "$total"
fi
