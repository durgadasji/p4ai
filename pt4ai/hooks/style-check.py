"""PostToolUse hook: check written files against your house style.

Your style, not anyone else's. The rules live in house-style.txt, one per line,
and the package ships none of its own as defaults. A writing rule is a taste
decision, and shipping one author's tastes as the built-in behaviour is the same
imposition as shipping their filing or their categories: it fires on every write,
so it is the most visible place to get that wrong.

Copy house-style.example.txt to get started and delete what you disagree with.
With no rules file this hook says so rather than passing silently.

Each line is a regular expression, matched case-insensitively. Put a plain word
or phrase and it works as you would expect. Comments start with #.

Never blocks. It also carries the shared exposure check, so the protection is
verified even in an installation where this is the only hook wired up.
"""

import sys, json, os, re, hashlib, subprocess, time, tempfile, tempfile


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

# Your rules, not anyone else's. Ships empty; see house-style.example.txt.
STYLE_FILE = os.environ.get("PRECISION_HOUSE_STYLE") or os.path.join(
    PRECISION_DIR, "house-style.txt")

# One run can have two things to say: a finding and an exposed inbox. Both are
# collected and printed once at the end, because two JSON objects on stdout do
# not parse as one and the whole message would be dropped.
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


def notice(msg, session):
    """Emit a configuration advisory once per session. Never blocks."""
    key = hashlib.md5(("style-check|" + session + "|" + msg).encode()).hexdigest()
    marker = os.path.join(TMP, "claude-hook-notice-" + key)
    if os.path.exists(marker):
        return
    try:
        open(marker, "w").close()
    except Exception:
        pass
    emit("STYLE-CHECK NOT RUNNING: " + msg)


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


def main():
    data = json.load(sys.stdin)
    session = data.get("session_id", "nosess") or "nosess"
    fp = (data.get("tool_input", {}) or {}).get("file_path", "") or ""

    check_precision_exposure(session, emit)

    if not fp:
        return

    rules = []
    try:
        with open(STYLE_FILE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    rules.append(line)
    except OSError:
        pass
    if not rules:
        notice("no rules in " + STYLE_FILE + ", so nothing about your writing is "
               "being checked. Copy house-style.example.txt and keep the rules "
               "you agree with.", session)
        return

    try:
        with open(fp, encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
    except OSError as err:
        emit("STYLE-CHECK NOT RUNNING: could not read " + fp + " (" +
             str(err) + "), so it is unchecked.")
        return

    hits = []
    for rule in rules:
        try:
            n = len(re.findall(rule, content, re.IGNORECASE))
        except re.error as err:
            notice("the rule " + rule + " in " + STYLE_FILE + " is not a valid "
                   "expression (" + str(err) + ") and was skipped.", session)
            continue
        if n:
            hits.append(rule + " (" + str(n) + ")")
    if hits:
        emit("HOUSE STYLE: " + str(len(hits)) + " rule(s) matched in " + fp +
             ": " + ", ".join(hits) + ". These are your rules, from " +
             STYLE_FILE + ".")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        try:
            emit("STYLE-CHECK ERROR: " + type(err).__name__ + ": " + str(err) +
                 ". The file was written and is unchecked.")
        except Exception:
            pass
    try:
        flush()
    except Exception:
        pass
    sys.exit(0)
