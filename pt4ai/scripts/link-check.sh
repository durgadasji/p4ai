#!/usr/bin/env bash
# link-check.sh: check that every link in authored content resolves.
#
# Scoped to authored files only. A first attempt scanned node_modules and spent
# its time reporting dead links inside third-party packages, which are neither
# yours nor actionable. Dependency and build output are excluded for the same
# reason the residue gate excludes them.
#
# Checks two classes:
#   - http(s) URLs, followed with redirects; anything that is not 2xx or 3xx
#     is reported with its status.
#   - relative markdown links to files in the same repository, which are the
#     ones most likely to break silently when a versioned filename moves. That
#     is how ten standard pointers became 404s without anyone noticing.
#
# Rate-limited hosts return 403 or 429 to a scripted request while working fine
# in a browser, so those are reported separately as unverified rather than as
# failures.
#
# Exit 0 = clean or only unverified. Exit 1 = at least one link is broken.
#
# Usage: bash link-check.sh [path]   (defaults to current directory)

set -u
target="${1:-.}"

echo "Link check of: $target"

files=$(find "$target" \
    \( -name node_modules -o -name .git -o -name dist -o -name build -o -name .next \) -prune -o \
    \( -name '*.md' -o -name '*.html' \) -print 2>/dev/null)

if [ -z "$files" ]; then
  echo "CLEAN: no authored markdown or html to check."
  exit 0
fi

broken=0
unverified=0

# --- relative links -------------------------------------------------------
# A broken internal link is the higher-signal failure: it means a file moved
# and something still points at where it was.
while IFS= read -r f; do
  [ -n "$f" ] || continue
  dir=$(dirname "$f")
  grep -oE '\]\([^)#][^)]*\)' "$f" 2>/dev/null \
    | sed 's/^](//; s/)$//' \
    | grep -vE '^(https?:|mailto:|#)' \
    | while IFS= read -r rel; do
        [ -n "$rel" ] || continue
        clean=${rel%%#*}
        [ -n "$clean" ] || continue
        if [ ! -e "$dir/$clean" ]; then
          echo "  BROKEN LINK  $f -> $rel"
        fi
      done
done <<< "$files" > /tmp/linkcheck-relative.$$ 2>/dev/null

if [ -s /tmp/linkcheck-relative.$$ ]; then
  echo ""
  echo "Relative links that do not resolve:"
  cat /tmp/linkcheck-relative.$$
  broken=1
fi
rm -f /tmp/linkcheck-relative.$$

# --- wikilinks ------------------------------------------------------------
# Nothing here assumes you keep a wiki. If no [[...]] links exist this section
# does nothing and says nothing. But if you do keep one, its links are the ones
# most likely to rot, and a checker that silently skips them reports CLEAN over
# a body of links it never read, which is the failure this whole gate is about.
#
# Resolution follows the wiki, not this script's guess: if a vault marker is
# found at or above the scanned path, links resolve against that root the way
# the wiki itself resolves them, and a miss is broken. Without a marker the root
# is unknown, a link may point somewhere above what was scanned, and misses are
# reported as unresolved rather than failed.
wikilinks=$(grep -rhoE '\[\[[^]|#]+' $files 2>/dev/null | sed 's/^\[\[//' | sort -u)

if [ -n "$wikilinks" ]; then
  # Marker directories of the note apps that use wikilinks. Set PRECISION_VAULT
  # to skip detection entirely, which is also the answer for an app not listed.
  # Nothing here requires any of them: with no marker and no override, the check
  # still runs, it simply reports unresolved rather than broken.
  vault="${PRECISION_VAULT:-}"
  if [ -z "$vault" ]; then
    probe=$(cd "$target" 2>/dev/null && pwd)
    while [ -n "$probe" ] && [ "$probe" != "/" ]; do
      for marker in .obsidian .logseq logseq .foam .silverbullet .zk; do
        if [ -d "$probe/$marker" ]; then vault="$probe"; break; fi
      done
      [ -n "$vault" ] && break
      probe=$(dirname "$probe")
    done
  fi
  root="${vault:-$target}"

  echo ""
  missing=""
  while IFS= read -r w; do
    [ -n "$w" ] || continue
    name=$(printf '%s' "$w" | sed 's/[[:space:]]*$//')
    if ! find "$root" -name "$name.md" -not -path '*/node_modules/*' -print -quit 2>/dev/null | grep -q .; then
      missing="$missing  $name"$'\n'
    fi
  done <<< "$wikilinks"

  if [ -n "$missing" ]; then
    if [ -n "$vault" ]; then
      echo "Wikilinks with no matching note (vault root: $vault):"
      printf '%s' "$missing"
      broken=1
    else
      echo "Wikilinks that did not resolve under $root, and no vault marker was"
      echo "found above it, so these may live outside what was scanned:"
      printf '%s' "$missing"
      unverified=1
    fi
  fi
fi

# --- absolute urls --------------------------------------------------------
# A URL written with a [variable] segment is a form to fill in. This pattern
# stops at the bracket, leaving a truncated address that never existed, so the
# truncated forms are excluded by name in the case block below rather than by
# widening this pattern. Adding brackets to the character class closes it early
# and matches nothing, which is a silent way to make every repo look clean.
urls=$(grep -rhoE 'https?://[A-Za-z0-9._~:/?#@!$&*+,;=%-]+' $files 2>/dev/null \
  | sed 's/[.,);:]*$//' \
  | sort -u)

if [ -n "$urls" ]; then
  echo ""
  for u in $urls; do
    case "$u" in
      # Not addresses: placeholders, illustrative examples, and templates whose
      # variable part this scan strips. Reporting these as broken taught me
      # nothing and buried the one link that was actually dead.
      *example.com*|*example.org*|*example-org*|*example-project*) continue ;;
      *localhost*|*127.0.0.1*) continue ;;
      # Referenced as specifications rather than visited.
      *schema.org*|*json-schema.org*|*w3.org*|*spdx.org*|*creativecommons.org*|*doi.org*) continue ;;
      # Preconnect and font-service origins. The bare origin 404s by design;
      # only the full stylesheet or font path resolves.
      https://fonts.googleapis.com|https://fonts.gstatic.com) continue ;;
    esac
    # A trailing path segment ending in a bare noun where the source had a
    # [placeholder] is a truncated template, not a link.
    case "$u" in
      */rfc|*/metric/|*/indicator/|*/id/) continue ;;
    esac
    code=$(curl -s -o /dev/null -w '%{http_code}' -L --max-time 10 \
             -A 'link-check (standards corpus)' "$u" 2>/dev/null)
    case "$code" in
      2*|3*) ;;
      000)   echo "  UNREACHABLE  $u"; unverified=1 ;;
      403|429) echo "  UNVERIFIED ($code, likely rate-limited)  $u"; unverified=1 ;;
      *)     echo "  BROKEN ($code)  $u"; broken=1 ;;
    esac
  done
fi

echo ""
if [ "$broken" -eq 1 ]; then
  echo "BROKEN LINKS FOUND."
  exit 1
fi
if [ "$unverified" -eq 1 ]; then
  echo "CLEAN, with some links unverified. Those need a browser, not a fix."
  exit 0
fi
echo "CLEAN: every link resolves."
exit 0
