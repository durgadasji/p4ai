"""PostToolUse hook: flag canon violations at the moment a governed file is written.

Rules live in a pattern file you maintain, holding the facts that must not drift:
dates, versions, counts, names. This hook is the fast local half, no network and
no binary scanning, so a wrong fact is caught as it is written rather than on a
later sweep. Pair it with a periodic check if you also need to see live surfaces
and files edited outside Claude.

Advisory, never blocking. A regex should not be able to stop a legitimate edit.

Misconfiguration reports itself rather than passing as silence. A hook that
cannot reach its pattern file is checking nothing, and a check nobody has seen
fail is a check they have no evidence about. Configuration problems surface once
per session as a visible notice. None of them block the write.

Pattern file format:

    {
      "scope":  ["/path/fragment/that/must/appear/in/the/file/path"],
      "exempt": ["/path/fragment/that/exempts/a/file"],
      "rules":  [
        {"id":      "short-id",
         "pattern": "regex, matched case-insensitively",
         "message": "what is wrong and what it should say",
         "unless":  "optional; a hit is ignored when its own line contains this"}
      ]
    }

"scope" is required and is a plain substring match against the written file's
path. A missing or empty "scope" matches no files, which is reported rather than
left to look like a clean result.
"""

import sys, json, re, os, hashlib, subprocess, time, tempfile

# This directory holds the terms your gates match against, which makes it the
# material whose publication would be worse than anything they catch. The
# pre-push scan verifies its protection too; this is the earlier net, since a
# write happens long before a push and the warning is more useful early.
#
# Every file in it is checked rather than a named one. A check that resolves a
# single filename covers that file and reports as though it covered the
# directory, so a second sensitive file sitting beside it is unguarded and
# nothing says so.
PRECISION_DIR = os.environ.get("PRECISION_DIR") or os.path.expanduser(
    "~/.claude/precision")

# How long a probe result stands before the check runs again. Long enough that
# the cost stays negligible across a long session, short enough that protection
# broken mid-session is caught while that session is still running rather than
# waiting for the next push. A still-exposed inbox warns again each interval,
# which is the intended nagging: it is not resolved until it is fixed.
PROBE_INTERVAL = 900  # seconds

# Not /tmp: that path does not exist on Windows.
TMP = tempfile.gettempdir()


def check_precision_exposure(session, report):
    """Verify nothing in the precision directory is exposed to git. One probe per
    interval, shared across every hook in this set: the marker key names the
    check rather than the hook, so whichever runs first does the work."""
    if not os.path.isdir(PRECISION_DIR):
        return
    marker = os.path.join(TMP, "claude-hook-notice-" + hashlib.md5(
        ("inbox-exposure|" + session).encode()).hexdigest())
    try:
        if time.time() - os.path.getmtime(marker) < PROBE_INTERVAL:
            return
    except OSError:
        pass  # no marker yet, so this is the first probe of the session
    d = PRECISION_DIR

    def git(*args):
        return subprocess.run(("git", "-C", d) + args, capture_output=True,
                              text=True, timeout=5).returncode

    exposed = []
    try:
        if git("rev-parse", "--is-inside-work-tree") != 0:
            return  # not in a repository, nothing to expose it
        for name in sorted(os.listdir(d)):
            if name == ".gitignore":
                continue
            f = os.path.join(d, name)
            if not os.path.isfile(f):
                continue
            # Tracking is checked first: an ignore rule does not reach a file git
            # already tracks, so one committed before the rule is published now.
            if git("ls-files", "--error-unmatch", f) == 0:
                exposed.append((name, "tracked"))
            elif git("check-ignore", "-q", f) != 0:
                exposed.append((name, "not ignored"))
    except Exception:
        return  # git unavailable or wedged; the pre-push gate still checks
    # Marked whether or not anything is wrong, so the cost is one probe per
    # interval rather than one per write. Still-exposed material warns again on
    # the next interval, and the pre-push gate remains the final backstop.
    try:
        open(marker, "w").close()
    except Exception:
        pass
    if exposed:
        report("PRECISION MATERIAL EXPOSED in " + d + ": " +
               "; ".join(n + " is " + why for n, why in exposed) +
               ". Anything tracked is already published, and 'git rm --cached' "
               "does not unpublish it. Anything unignored is one 'git add -A' "
               "from the same place. The rule lives in " +
               os.path.join(d, ".gitignore") + ".")

# Your pattern file, beside your other answers. It lives there rather than as a
# constant in this file because a setting edited into shipped source is a setting
# a plugin update silently reverts, and the person who loses it has no way to
# know: the hook goes on running and simply stops checking what it used to.
# PRECISION_CANON overrides it for a one-off run against a different set.
PATTERNS = os.environ.get("PRECISION_CANON") or os.path.join(
    PRECISION_DIR, "canon-patterns.json")


def notice(msg, session):
    """Emit a configuration advisory once per session. Never blocks."""
    key = hashlib.md5(("canon-check|" + session + "|" + msg).encode()).hexdigest()
    marker = os.path.join(TMP, "claude-hook-notice-" + key)
    if os.path.exists(marker):
        return
    try:
        open(marker, "w").close()
    except Exception:
        pass
    emit("CANON-CHECK NOT RUNNING: " + msg)


# One run can have several things to say: an unconfigured gate, a malformed
# rule, a finding, an exposed inbox. Each is collected and printed once at the
# end, because two JSON objects on stdout do not parse as one and the whole
# message would be dropped.
_MESSAGES = []


def emit(msg):
    _MESSAGES.append(msg)


def flush():
    if not _MESSAGES:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n\n".join(_MESSAGES),
        }
    }))


def main():
    data = json.load(sys.stdin)
    session = data.get("session_id", "nosess") or "nosess"
    fp = (data.get("tool_input", {}) or {}).get("file_path", "") or ""
    if not fp or not os.path.isfile(fp):
        return

    check_precision_exposure(session, emit)

    try:
        with open(PATTERNS, encoding="utf-8") as fh:
            canon = json.load(fh)
    except FileNotFoundError:
        notice("no pattern file at " + PATTERNS + ", so this hook is checking "
               "nothing.", session)
        return
    except ValueError as err:
        notice("the pattern file at " + PATTERNS + " is not valid JSON (" +
               str(err) + "), so this hook is checking nothing.", session)
        return
    except OSError as err:
        notice("the pattern file at " + PATTERNS + " could not be read (" +
               str(err) + "), so this hook is checking nothing.", session)
        return

    scope = canon.get("scope") or []
    if not scope:
        notice("the pattern file at " + PATTERNS + " has no non-empty \"scope\" "
               "key, so it matches no file and this hook is checking nothing.",
               session)
        return

    if not any(s in fp for s in scope):
        return
    if any(e in fp for e in canon.get("exempt", [])):
        return

    with open(fp, encoding="utf-8", errors="ignore") as fh:
        content = fh.read()

    findings = []
    for rule in canon.get("rules", []):
        try:
            hits = list(re.finditer(rule["pattern"], content, re.IGNORECASE))
        except KeyError:
            notice("a rule in " + PATTERNS + " has no \"pattern\" key and was "
                   "skipped.", session)
            continue
        except re.error as err:
            notice("rule " + str(rule.get("id", "?")) + " in " + PATTERNS +
                   " is not a valid regex (" + str(err) + ") and was skipped, "
                   "so that fact is unchecked.", session)
            continue
        if not hits:
            continue
        unless = rule.get("unless")
        if unless:
            # Keep only hits whose surrounding line lacks the required qualifier.
            kept = []
            for m in hits:
                start = content.rfind("\n", 0, m.start()) + 1
                end = content.find("\n", m.end())
                line = content[start: end if end != -1 else len(content)]
                if unless.lower() not in line.lower():
                    kept.append(m)
            hits = kept
            if not hits:
                continue
        line_no = content.count("\n", 0, hits[0].start()) + 1
        findings.append("  [{}] line {}: {}".format(
            rule.get("id", "?"), line_no, rule.get("message", "canon violation")))

    if findings:
        emit("CANON ALERT in " + os.path.basename(fp) + ":\n"
             + "\n".join(findings)
             + "\nAuthority: your canon pattern file. Fix now rather than "
               "deferring; this is a governed surface.")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        # Never block a write, and never let the failure pass as a clean result.
        try:
            emit("CANON-CHECK ERROR: " + type(err).__name__ + ": " + str(err) +
                 ". The file was written and is unchecked.")
        except Exception:
            pass
    try:
        flush()
    except Exception:
        pass
    sys.exit(0)
