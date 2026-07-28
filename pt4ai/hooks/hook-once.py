"""Reminder scheduler for standing obligations that need restating rather than testing.

Most entries fire once per file per session, scoped to a path pattern you set.
One does not: `readfirst` is marked always, meaning no path pattern, no file
argument and no dedupe, so it restates on every mutating call it is wired to.
That asymmetry is the point rather than an oversight, and the comment on that
entry says why.

Each entry is selected by an id passed as the first argument, so this file is
wired into settings.json once per obligation:

    python3 ~/.claude/hooks/hook-once.py threereader     (PreToolUse)
    python3 ~/.claude/hooks/hook-once.py readfirst       (PreToolUse)
    python3 ~/.claude/hooks/hook-once.py versionbump     (PostToolUse)

Without an id it has nothing to fire, and a placeholder left in an include
pattern matches no path. Both conditions report themselves once per session
rather than passing as silence, because a reminder that never arrives looks
exactly like a reminder that was not needed. Nothing here blocks a write.
"""

import sys, json, os, hashlib, re, subprocess, time, tempfile

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

# Optional tail appended to the read-first message, for the specifics of your own
# material. Left empty the obligation still stands in its general form. Filled in,
# the reminder names the particular canonical files and the particular searches
# your work depends on, which is where a general rule becomes something you can
# actually be held to. Keep it to a sentence or two. For example:
#
#     LOCAL = (" In this corpus specifically: reference/index.md is the canonical"
#              " copy and the dated files beside it are snapshots; search the"
#              " topic folders including one query framed to disconfirm.")
LOCAL = ""

HOOKS = {
    # The exclude ships filled in, because which files are not documents is a
    # general finding rather than one person's filing: indexes, readmes, memory
    # files, handoffs, inboxes, logs and tool configuration are working material,
    # and an obligation that fires on them teaches people to dismiss it. Add your
    # own working directories to the second group. The include stays a
    # placeholder because only you know where your documents live.
    "threereader": {
        "event": "PreToolUse",
        "include": r"/YOUR_NOTES_DIR/.*\.md$",
        "exclude": r"/(handoff[^/]*|index|MEMORY|README)\.md$|/(inbox|log)/|/\.claude/",
        "message": "STANDING OBLIGATION (Three-Reader Standard): this is a substantive document. Confirm it is followable by a general reader, usable by a practitioner, and testable by a researcher. Flag any passage that fails one of the three.",
    },
    # Always: no path pattern, no per-file dedupe, no file argument required.
    # Read-first is a general instruction rather than a rule about particular
    # directories, and an allowlist of directories is exactly how it comes to
    # fire on nothing that matters. Any pattern narrower than every mutating
    # call will miss the case you most needed it for, because that is the case
    # you did not think of while writing the pattern. It repeats rather than
    # deduping for the same reason: the moment it is most needed is the moment
    # it feels least necessary.
    "readfirst": {
        "event": "PreToolUse",
        "always": True,
        "message": "STANDING OBLIGATION (read-first), which always applies and is not restricted to particular paths or document types: read the actual source before building, editing, or asserting. Not a summary, not a handoff, not a prior extract, not memory of it. Establish which copy is canonical before reading any of them, because filenames carry versions and versions move. If a command can verify a claim, run it before saying it, and that binds hardest on facts stated in passing as background rather than offered as findings. Building or asserting before reading is a top-priority violation and does not yield to time pressure." + LOCAL,
    },
    # Which directories hold versioned documents is a fact about your corpus, so
    # the include stays a placeholder rather than shipping somebody's taxonomy as
    # a general one. It takes a list, because a corpus that versions anything
    # usually versions several kinds of thing. For example:
    #
    #     "include": r"/(standards|specifications|reference)/",
    "versionbump": {
        "event": "PostToolUse",
        "include": r"/YOUR_VERSIONED_DOCS_DIR/",
        "exclude": "",
        "message": "STANDING OBLIGATION: you just edited a versioned corpus document. Bump the version in the frontmatter and add a changelog entry, unless this was only a correction.",
    },
}

# Any of these left in an include or exclude pattern means that entry was never
# pointed at a real path and will never fire.
PLACEHOLDERS = ("YOUR_NOTES_DIR", "YOUR_VERSIONED_DOCS_DIR")


# One run can have several things to say: the obligation itself, and an exposed
# inbox. Both are collected and printed once at the end, because two JSON
# objects on stdout do not parse as one and the whole message would be dropped.
_MESSAGES = []
_EVENT = ["PreToolUse"]


def emit(event, msg):
    _EVENT[0] = event
    _MESSAGES.append(msg)


def flush():
    if not _MESSAGES:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": _EVENT[0],
            "additionalContext": "\n\n".join(_MESSAGES),
        }
    }))


def notice(event, msg, session):
    """Emit a configuration advisory once per session. Never blocks."""
    key = hashlib.md5(("hook-once|" + session + "|" + msg).encode()).hexdigest()
    marker = os.path.join(TMP, "claude-hook-notice-" + key)
    if os.path.exists(marker):
        return
    try:
        open(marker, "w").close()
    except Exception:
        pass
    emit(event, "HOOK-ONCE NOT RUNNING: " + msg)


def main():
    data = json.load(sys.stdin)
    session = data.get("session_id", "nosess") or "nosess"
    # The payload names its own event, which is the only way to answer correctly
    # when the id that would have named it is the thing that is missing.
    event = data.get("hook_event_name") or "PreToolUse"

    check_precision_exposure(session, lambda m: emit(event, m))

    hid = sys.argv[1] if len(sys.argv) > 1 else ""
    if not hid:
        notice(event, "this hook was invoked with no id, so it has nothing to "
                      "fire. Wire it once per obligation, passing one of: "
                      + ", ".join(sorted(HOOKS)) + ".", session)
        return
    if hid not in HOOKS:
        notice(event, "\"" + hid + "\" is not a known id, so nothing fired. "
                      "Known ids: " + ", ".join(sorted(HOOKS)) + ".", session)
        return

    cfg = HOOKS[hid]

    if cfg.get("always"):
        # No path pattern, no file argument, no dedupe. Fires on every mutating
        # call it is wired to, which is the whole point of this entry.
        emit(cfg["event"], cfg["message"])
        return

    stale = [p for p in PLACEHOLDERS
             if p in cfg.get("include", "") or p in (cfg.get("exclude") or "")]
    if stale:
        notice(cfg["event"], "the \"" + hid + "\" entry still contains the "
               "placeholder " + ", ".join(stale) + " in its path pattern, so it "
               "matches no file and will never fire. Point it at your own "
               "layout, or remove this entry from settings.json.", session)
        return

    fp = (data.get("tool_input", {}) or {}).get("file_path", "") or ""
    if not fp:
        return
    try:
        if not re.search(cfg["include"], fp):
            return
        if cfg["exclude"] and re.search(cfg["exclude"], fp):
            return
    except re.error as err:
        notice(cfg["event"], "the \"" + hid + "\" entry has an invalid path "
               "pattern (" + str(err) + "), so it fires on nothing.", session)
        return

    key = hashlib.md5((hid + "|" + session + "|" + fp).encode()).hexdigest()
    marker = os.path.join(TMP, "claude-hookonce-" + key)
    if os.path.exists(marker):
        return
    open(marker, "w").close()
    emit(cfg["event"], cfg["message"])


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        # Never block a write, and never let the failure pass as a clean result.
        try:
            emit("PreToolUse", "HOOK-ONCE ERROR: " + type(err).__name__ + ": "
                 + str(err) + ". The reminder did not fire.")
        except Exception:
            pass
    try:
        flush()
    except Exception:
        pass
    sys.exit(0)
