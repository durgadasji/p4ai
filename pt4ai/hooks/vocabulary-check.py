"""Vocabulary gate: flag watchlist terms in your own writing, at the moment you write them.

Optional. This one only makes sense if you keep a vocabulary discipline, and it
ships alongside the Frame Language standard rather than as part of the base set.
Install it if you want that discipline checked rather than intended.

Where the terms come from. A local registry file, and only a local file. The
install step fetches the published one once, with you watching; after that this
hook never reaches the network, so nothing about your machine or your writing
leaves it. Refresh deliberately when you want to, and the age of what you have
is reported so a stale list is visible rather than assumed current.

Where it looks. Nothing is assumed about your filing. Put path fragments in
vocabulary-scope.txt, one per line, naming the writing you want held to the
standard, and optionally vocabulary-skip.txt for the places you do not: logs,
scratch, notes to yourself, wherever the watchlist terms are ordinary rather
than drift. With no scope file it says so instead of checking nothing quietly.

Non-blocking: it reminds, it does not stop the edit. Admissibility stays a
judgment made at edit time, since quoting a source and naming a term as the
subject of analysis are both legitimate and neither is detectable from here.
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
# waiting for the next push. Still-exposed material warns again each interval,
# which is the intended nagging: it is not resolved until it is fixed.
PROBE_INTERVAL = 900  # seconds

# The registry, on disk. This hook makes no network calls at all: fetching is an
# install-time act you perform and can watch, not something a write-time hook
# does on your behalf. A tool that reads your files has no business also opening
# connections, whatever it claims to send.
REGISTRY_FILE = os.environ.get("PRECISION_REGISTRY") or os.path.join(
    PRECISION_DIR, "term-registry.json")

# Beyond this, the copy on disk is old enough to mention. Not an error: a stale
# list still checks, and silence about its age is what would be wrong.
STALE_AFTER = 90 * 24 * 60 * 60  # seconds

SCOPE_FILE = os.path.join(PRECISION_DIR, "vocabulary-scope.txt")
SKIP_FILE = os.path.join(PRECISION_DIR, "vocabulary-skip.txt")

TMP = tempfile.gettempdir()

# One run can have several things to say: an unconfigured gate, a finding,
# exposed material. Each is collected and printed once at the end, because two
# JSON objects on stdout do not parse as one and the message would be dropped.
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
    key = hashlib.md5(("vocabulary-check|" + session + "|" + msg).encode()).hexdigest()
    marker = os.path.join(TMP, "claude-hook-notice-" + key)
    if os.path.exists(marker):
        return
    try:
        open(marker, "w").close()
    except Exception:
        pass
    emit("VOCABULARY-CHECK NOT RUNNING: " + msg)


def read_list(path):
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    out.append(line)
    except OSError:
        pass
    return out


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


def load_registry(session):
    """Return (terms, version, source) or (None, None, None) after reporting why.

    Local only. Nothing here opens a connection.
    """
    try:
        with open(REGISTRY_FILE, encoding="utf-8") as fh:
            reg = json.load(fh)
    except FileNotFoundError:
        notice("no registry at " + REGISTRY_FILE + ", so this gate has no terms "
               "and passes every file. Fetch one during install, or point "
               "PRECISION_REGISTRY at your own.", session)
        return None, None, None
    except Exception as err:
        notice("the registry at " + REGISTRY_FILE + " is unusable (" + str(err) +
               "), so this gate has no terms and passes every file.", session)
        return None, None, None

    terms, version = terms_of(reg)
    source = REGISTRY_FILE
    try:
        age = time.time() - os.path.getmtime(REGISTRY_FILE)
        if age > STALE_AFTER:
            source += " (last updated " + str(int(age / 86400)) + " days ago)"
    except OSError:
        pass
    return terms, version, source


def terms_of(reg):
    terms = [t["term"] for t in reg.get("terms", [])
             if isinstance(t, dict) and "term" in t]
    return terms, reg.get("version", "?")


def main():
    data = json.load(sys.stdin)
    session = data.get("session_id", "nosess") or "nosess"
    fp = (data.get("tool_input", {}) or {}).get("file_path", "") or ""

    # Before the path filters, so the precision directory is checked on any write
    # rather than only on writes this gate happens to be scoped to.
    check_precision_exposure(session, emit)

    if not fp or not fp.endswith(".md"):
        return

    scope = read_list(SCOPE_FILE)
    if not scope:
        notice("no paths in " + SCOPE_FILE + ", so this gate does not know "
               "which writing you want held to the standard and is checking "
               "nothing. Put one path fragment per line there.", session)
        return
    if not any(s in fp for s in scope):
        return
    if any(s in fp for s in read_list(SKIP_FILE)):
        return

    terms, version, source = load_registry(session)
    if not terms:
        if terms is not None:
            notice("the registry carries no usable terms, so this gate passes "
                   "every file.", session)
        return

    with open(fp, encoding="utf-8", errors="ignore") as fh:
        content = fh.read()

    hits = []
    for term in terms:
        n = len(re.findall(r"\b" + re.escape(term) + r"\b", content, flags=re.IGNORECASE))
        if n:
            hits.append((term, n))

    if hits:
        hits.sort(key=lambda x: (-x[1], x[0]))
        listed = ", ".join("%s (%d)" % (t, n) for t, n in hits)
        emit(
            "VOCABULARY ALERT (registry v" + str(version) + " from " + source +
            "): " + str(len(hits)) + " watchlist term(s) in " + fp + ": " + listed
            + ". For each use in your own voice, replace it with language naming "
            "who does what to whom. Leave it only where an exception applies: "
            "quoting a source, or naming the term as the subject of analysis. "
            "Do not rely on a later catch."
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        # Never block a write, and never let the failure pass as a clean result.
        try:
            emit("VOCABULARY-CHECK ERROR: " + type(err).__name__ + ": " + str(err) +
                 ". The file was written and is unchecked.")
        except Exception:
            pass
    try:
        flush()
    except Exception:
        pass
    sys.exit(0)
