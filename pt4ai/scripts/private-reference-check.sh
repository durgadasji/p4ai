#!/usr/bin/env bash
# private-reference-check.sh: flag references to private repositories in
# public-bound material.
#
# This closes the gap residue-scan.sh documents but cannot cover: a plain
# private filename cited without your working prefix in its path. A hand-kept
# denylist catches such a reference only if someone thought to add that exact
# name, and most of them look like nothing: there is nothing about
# "parsec/lib/analyze.ts" that reads as private.
#
# The mechanism keys on local checkout names, because that is how such
# references are actually written. A document says "parsec/lib/analyze.ts",
# meaning the local directory ~/code/parsec, whose git remote is a private
# repository. Asking a hosting API about "parsec" finds nothing, so an API-only
# check misses it, quite apart from the fact that asking means sending the
# private name to someone.
#
# The name here is invented. A real one would make this file the thing it warns
# about, and the lesson does not need a real name to land: the whole point is
# that a plain directory name looks like nothing either way.
#
# For every path-like reference in the scanned material, take the leading
# segment and see whether a checkout of that name exists locally. If it does and
# you have not declared it safe to name, the reference is flagged. Declaring is
# a local file you maintain; nothing is asked of any server.
#
# Keep an alias map beside it if you publish about private work: a table of real
# name to published name, so the writing can refer to something consistently
# without naming the thing itself.
#
# Exit 0 = clean or undeterminable. Exit 1 = a private reference was found.
#
# Usage: bash private-reference-check.sh [path] [checkout-root]
#   defaults: current directory, ~/code

set -u
target="${1:-.}"
root="${2:-$HOME/code}"

echo "Private-reference check of: $target"

# Which of your checkouts are safe to name in public, one per line, in
# ~/.claude/precision/public-repos.txt. A checkout name or a full slug both work.
#
# The question is deliberately "have you said this one is safe to name" rather
# than "is this public". Resolving visibility over the network would invert the
# whole point: establishing that a reference is private by transmitting the
# private name to a third party, including for repositories not hosted there and
# whose names that party has no reason to learn. A privacy gate must not be the
# leak. Asking locally works offline, works for any host, and fails toward
# silence rather than toward exposure.
PUBLIC_REPOS="${PRECISION_PUBLIC_REPOS:-${PRECISION_DIR:-$HOME/.claude/precision}/public-repos.txt}"

is_public() {
  [ -f "$PUBLIC_REPOS" ] || return 1
  grep -qiE "(^|/)$1[[:space:]]*$" "$PUBLIC_REPOS" 2>/dev/null
}

# Path-like references: a leading segment followed by a slash and more path.
# Restricted to segments that look like project directory names.
# Every text file, with no type allowlist. A type allowlist reads only what
# someone thought to list, and these gates ship as .sh, so any list that omits
# it leaves the checks unable to read each other. Binary files are skipped
# with -I.
candidates=$(grep -rhoIE '\b[a-z][a-z0-9]+(-[a-z0-9]+)*/(lib|src|app|packages|scripts|docs)/[A-Za-z0-9._/-]+' "$target" \
    2>/dev/null \
  | grep -v '/node_modules/' \
  | cut -d/ -f1 \
  | sort -u)

if [ -z "$candidates" ]; then
  echo "CLEAN: no path-like references to resolve."
  exit 0
fi

found=0
checked=0

for name in $candidates; do
  dir="$root/$name"
  [ -d "$dir/.git" ] || continue

  # The remote is read locally and never contacted. It is used only to let you
  # list either the checkout name or the full slug in public-repos.txt.
  url=$(git -C "$dir" remote get-url origin 2>/dev/null) || url=""
  slug=$(printf '%s' "$url" | sed 's|.*[:/]\([^/]*/[^/]*\)$|\1|; s|\.git$||')

  checked=$((checked + 1))

  if is_public "$name" || { [ -n "$slug" ] && is_public "$slug"; }; then
    continue
  fi

  echo "UNDECLARED REFERENCE: '$name/'${slug:+ (remote $slug)} is not listed as public."
  echo "  Either add it to $PUBLIC_REPOS, or replace the reference with an alias."
  grep -rnIE "\b$name/(lib|src|app|packages|scripts|docs)/" "$target" 2>/dev/null \
    | grep -v '/node_modules/' | sed 's/^/    /' | head -5
  found=1
done

if [ "$found" -eq 1 ]; then
  echo "UNDECLARED REFERENCES FOUND, do NOT push until each is declared or aliased."
  exit 1
fi

if [ "$checked" -eq 0 ]; then
  # Nothing was resolved, which is not the same as nothing being wrong. Saying
  # "clean" here would claim a verification that never ran.
  echo "NOTHING TO CHECK: references were found, but none resolve to a checkout"
  echo "  under $root, so their visibility was never established. Point the"
  echo "  second argument at your checkout root if it lives elsewhere."
  exit 0
fi

echo "CLEAN: $checked referenced checkout(s), each declared public in $PUBLIC_REPOS."
exit 0
