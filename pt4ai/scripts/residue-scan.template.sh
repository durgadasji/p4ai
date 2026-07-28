#!/usr/bin/env bash
# residue-scan.sh: standing pre-publish gate.
#
# Run this against any repo or directory BEFORE pushing it anywhere public. It
# flags material you have designated as private, so it is caught while it is
# still yours to catch.
#
# It ships with no categories. What counts as private, and how you divide it up,
# is yours to designate: this file holds the mechanism and reads your terms from
# a list you keep. A built-in taxonomy would be one person's filing shipped as a
# general fact, and it would also disclose that filing, since a list of what to
# look for is a negative image of what is being protected.
#
# Two checks are built in because they are general rather than anybody's:
#   - the em dash (house writing rule), detected via a built character so this
#     file holds no literal one
#   - references to your working documents, matched by the prefix you set
#
# Everything else comes from your terms file, one pattern per line. Group them
# however you like with comments; nothing here needs to know your groupings.
#
# Every text file is scanned. There is no file-type allowlist, because an
# allowlist reads only the types someone thought to list, and these gates ship
# as .sh, so any list omitting it cannot read the files this package is made of.
# Binary files are skipped with grep -I.
#
# It also excludes node_modules, dist, .next and build. Those are dependency and
# build output, not authored content. Without this the gate cannot pass on any
# Node repository at all: third-party packages contain em dashes in their own
# READMEs, so every run reported residue that was never yours.
#
# Expect collisions between your terms and published vocabulary. A word that
# marks private material in your filing can be a defined term in somebody's
# public specification, and the scan cannot tell the two apart. Put those exact
# strings in your exempt file rather than weakening the term, and note why. Name
# checks collide the same way: if a published author shares a surname with
# someone on your list, exempt that exact citation string rather than dropping
# the name.
#
# Exit 0 = clean. Exit 1 = residue found, do not push.
#
# Usage: bash residue-scan.sh [path]   (defaults to current directory)
#
# Note: this catches what you can state as a pattern. It does not replace the
# human check for the two softer classes that need judgment each time:
#   (a) a plain private filename carrying none of your working prefix in its
#       path, named in a public changelog or sources list;
#   (b) private content dressed as an illustrative example.

set -u
target="${1:-.}"

# --- exposure check on the directory that arms this scan --------------------
# That directory holds the terms this scan matches against, which makes it the
# material whose publication would be worse than anything the scan catches: a
# denylist is a negative image of what it guards. The rule protecting it lives
# in a committed .gitignore and is a deleted line away from gone, so it is
# verified here rather than trusted.
#
# Every file in it is checked, not a named one. A check that resolves a single
# filename covers that file and reports as though it covered the directory, so a
# second sensitive file beside it is unguarded and nothing says so.
#
# Tracking is checked before ignoring, because an ignore rule does not apply to
# a file git already tracks. Adding the rule after the commit changes nothing,
# and a check that reported "ignored, therefore safe" in that case would be
# reporting clean about a file that is already published.
PRECISION_DIR="${PRECISION_DIR:-$HOME/.claude/precision}"

check_precision_exposure() {
  [ -d "$PRECISION_DIR" ] || return 0
  git -C "$PRECISION_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0

  repo=$(git -C "$PRECISION_DIR" rev-parse --show-toplevel 2>/dev/null)
  bad=0

  for f in "$PRECISION_DIR"/* "$PRECISION_DIR"/.[!.]*; do
    [ -f "$f" ] || continue
    case "${f##*/}" in .gitignore) continue ;; esac

    if git -C "$PRECISION_DIR" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      echo "TRACKED BY GIT: $f"
      echo "  It is committed, so the ignore rule does not reach it and will not"
      echo "  remove it. Untrack it with 'git rm --cached' and treat everything"
      echo "  in it as already published."
      bad=1
    elif ! git -C "$PRECISION_DIR" check-ignore -q "$f"; then
      echo "NOT IGNORED: $f"
      echo "  Nothing stops the next 'git add -A' from committing it."
      bad=1
    fi
  done

  [ "$bad" -eq 0 ] || echo "  Repository: $repo"
  return "$bad"
}

if ! check_precision_exposure; then
  echo ""
  echo "Refusing to pass: the material that arms this scan is exposed."
  exit 1
fi

emdash=$(printf '\xe2\x80\x94')

# The prefix marking your accumulated working and research documents, the ones
# that are not meant to leave. Asked rather than assumed. Whatever word you use
# is a fact about your filing rather than a general one, and a default that
# happened to fit nobody would check nothing while looking like it checked
# something. Leave it unset and this class stays unchecked, which the scan says
# out loud rather than passing over in silence.
#
# It lives beside your other answers so the install inquiry writes it the same
# way it writes everything else. The environment variable still wins when set,
# which is what a one-off run against different filing needs.
WORKING_PREFIX_FILE="${PRECISION_WORKING_PREFIX_FILE:-$PRECISION_DIR/working-prefix.txt}"

# Your designated terms, one pattern per line. Blank lines and lines beginning
# with # are ignored, so you can group and annotate them however you think about
# them. This file is as sensitive as the inbox: it is the same negative image,
# so keep it in the same ignored location.
#
# The install inquiry writes these; the environment overrides them for a one-off
# run against a different set.
TERMS="${PRECISION_TERMS:-$PRECISION_DIR/terms.txt}"
EXEMPT="${PRECISION_EXEMPT:-$PRECISION_DIR/exempt.txt}"

read_list() {
  [ -f "$1" ] || return 0
  grep -vE '^\s*(#|$)' "$1" 2>/dev/null | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

# Resolved here rather than above because it reads a file and read_list is the
# reader. First non-comment line wins: this is one value, not a list, and a file
# with several lines in it is a filing convention that has not been decided yet.
WORKING_PREFIX="${PRECISION_WORKING_PREFIX:-$(read_list "$WORKING_PREFIX_FILE" | head -1)}"

term_count=0
patterns="$emdash"
if [ -f "$TERMS" ]; then
  while IFS= read -r t; do
    [ -n "$t" ] || continue
    patterns="$patterns|$t"
    term_count=$((term_count + 1))
  done <<< "$(read_list "$TERMS")"
fi
if [ -n "$WORKING_PREFIX" ]; then
  patterns="$patterns|${WORKING_PREFIX}[-/]"
fi

exempt=""
while IFS= read -r e; do
  [ -n "$e" ] || continue
  exempt="${exempt:+$exempt|}$e"
done <<< "$(read_list "$EXEMPT")"

echo "Residue scan of: $target"

# What is and is not armed, stated before the result, so a clean report can be
# read for what it actually covers.
if [ -z "$WORKING_PREFIX" ]; then
  echo "NOT CHECKING working-document references: no prefix in $WORKING_PREFIX_FILE, and PRECISION_WORKING_PREFIX is unset."
fi
if [ "$term_count" -eq 0 ]; then
  echo "NOT CHECKING designated terms: no terms found at $TERMS."
  echo "  Only the em dash rule is armed. A clean result below means very little."
else
  age=""
  if command -v date >/dev/null 2>&1; then
    age=$(( ( $(date +%s) - $(stat -f %m "$TERMS" 2>/dev/null || stat -c %Y "$TERMS" 2>/dev/null || echo 0) ) / 86400 ))
  fi
  echo "Checking $term_count designated term(s) from $TERMS${age:+, last changed ${age}d ago}."
  if [ -n "$age" ] && [ "$age" -gt 90 ]; then
    echo "  A list that has not moved in ${age} days is a question, not a result:"
    echo "  yours grows when something nearly leaks, so a still list means either"
    echo "  nothing came close or nothing was added."
  fi
fi

hits=$(grep -rnIiE "$patterns" "$target" 2>/dev/null \
      | grep -v '/\.git/' \
      | grep -v '/node_modules/' \
      | grep -v '/dist/' \
      | grep -v '/\.next/' \
      | grep -v '/build/')
if [ -n "$exempt" ]; then
  hits=$(printf '%s\n' "$hits" | grep -viE "$exempt")
fi
hits=$(printf '%s' "$hits" | grep -v '^$' || true)

if [ -n "$hits" ]; then
  echo "RESIDUE FOUND, do NOT push until resolved:"
  echo "$hits"
  exit 1
else
  echo "CLEAN: nothing matched what is armed above."

  # A term list only catches what someone thought to add. The private-reference
  # check resolves referenced checkouts against their remotes instead, which
  # needs no list and covers the soft class this script cannot: a plain private
  # filename that looks like nothing.
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [ -f "$here/private-reference-check.sh" ]; then
    echo ""
    if ! bash "$here/private-reference-check.sh" "$target"; then
      echo ""
      echo "Residue patterns were clean but a private repository is referenced."
      echo "Alias it before pushing."
      exit 1
    fi
  fi

  echo ""
  echo "Reminder: still eyeball for private content dressed as an example, and for names too common to automate. A name that also appears in a legitimate public citation will false-positive, so those stay a human check rather than a pattern."
  exit 0
fi
