#!/usr/bin/env python3
"""Sensemaking gate.

Forces an explicit approval prompt before any file-mutating tool touches
authored, conceptual or notes content. Reads the PreToolUse JSON on stdin,
returns permissionDecision "ask" for guarded targets, and otherwise stays
silent so normal permission flow is unchanged. Never hard-blocks; "ask"
overrides acceptEdits / bypassPermissions so nothing lands without a click.

The prompt asks the Sensemaking Standard's own tests rather than whether
sensemaking is "complete". Under SMS 1.1.23 Invariant 3.4 the terminal state
is sufficiency, and reaching a state where nothing is unresolved is the marker
that the process has crossed into analysis; under 3.3, a rule barring the write
until understanding is complete is the analysis-paralysis violation by name.
The gate is on whether a frame actually changed, not on whether writing waits.
"""
import sys, json, unicodedata, os, hashlib, subprocess, time, re, tempfile

# Not /tmp: that path does not exist on Windows, and this package is meant
# to run wherever Claude Code runs.
TMP = tempfile.gettempdir()

# This directory holds the terms your gates match against, which makes it the
# material whose publication would be worse than anything they catch. The pre-push scan
# verifies its protection too; this is the earlier net, since a write happens
# long before a push and the warning is more useful early than late.
PRECISION_DIR = os.environ.get("PRECISION_DIR") or os.path.expanduser(
    "~/.claude/precision")

# How long a probe result stands before the check runs again. Long enough that
# the cost stays negligible across a long session, short enough that protection
# broken mid-session is caught while that session is still running rather than
# waiting for the next push. A still-exposed inbox warns again each interval,
# which is the intended nagging: it is not resolved until it is fixed.
PROBE_INTERVAL = 900  # seconds

REASON = (
    "Sensemaking gate, per the Sensemaking Standard 1.1.23. This is not a "
    "completeness check: stopping at sufficiency is correct, and continuing "
    "until nothing is unresolved means this has become analysis (3.4). "
    "Confirm with the author before this lands. "
    "(1) Name the disruption that occasioned this work, or say there is none "
    "and that what follows is execution rather than sensemaking (3.1). "
    "(2) Confirm the frame about to be written differs from one already "
    "available before starting, and that the interval of not-knowing can be "
    "pointed at; if the transition was instantaneous this is recognition, not "
    "sensemaking (3.5). "
    "(3) Record it as provisional, with its revision conditions and the "
    "questions deliberately left unpursued (3.4). "
    "(4) State its initiating disruption, the frame it produced, and the "
    "evidence basis for that frame, because whoever reads it next did not "
    "take part in the process that produced it (2.3, 4.3)."
)

# Where your material lives, one absolute path per line, in
# ~/.claude/precision/guarded-roots.txt. Blank lines and # are ignored, and ~ is
# expanded, so the file reads as a list of places rather than a config format.
#
# This is asked rather than compiled in. Editing Python to say where your notes
# are is a barrier, and worse, a list left at its defaults guards nothing while
# looking installed. If the file is missing or empty the gate says so instead of
# standing silently by, because a gate that never fires and a gate with nothing
# to fire on look identical from outside.
GUARDED_ROOTS_FILE = os.path.join(PRECISION_DIR, "guarded-roots.txt")


def guarded_roots():
    roots = []
    try:
        with open(GUARDED_ROOTS_FILE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    roots.append(os.path.expanduser(line))
    except OSError:
        pass
    return roots

# Bounded, scoped stand-down, for a stretch of work that should keep running
# while you are not at the keyboard.
#
# The case this exists for is stepping away mid-batch. Pausing the prompts is not
# the same as pausing the work, and with no way to say that, the only options are
# sitting there clicking or killing the hook. A gate with no way out gets deleted
# rather than paused, and a hook deleted on one tiring afternoon is gone for good.
#
# The marker holds one path prefix per line, so a pause is scoped and does not
# unguard everything else. An optional "minutes: N" line sets the duration; with
# no such line it runs for DEFAULT_PAUSE_MINUTES. It expires by itself, because
# an off switch that has to be remembered is the permanent state in disguise.
# Touch the file to restart the clock, delete it to end the pause now.
#
# A pause is bounded three ways, and the third is easy to miss. Scope, expiry,
# and the turn: it suppresses the prompt inside work already underway and
# authorizes nothing new, so the work still stops when it is done and waits. A
# long duration is therefore not a long stretch of unattended writing.
#
# It is never silent: every paused write says so and counts down, so what landed
# without a prompt stays visible rather than implicit.
PAUSE = os.path.join(PRECISION_DIR, "gate-pause")
DEFAULT_PAUSE_MINUTES = 45

FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Notes reached through an MCP server, whatever server that is.
#
# Naming the tools you happen to use is the same allowlist mistake as naming the
# paths or the file types you happen to have: it fires on what someone thought to
# list, so one app's notes are guarded and everyone else's are quietly not.
#
# The test is on the verb instead. Any MCP tool whose name carries a mutating
# word is treated as a write, which covers note apps nobody here has heard of.
# The bias is deliberate and it runs opposite to the residue scan's: for a gate,
# a false positive costs one approval click and a false negative is an unguarded
# write, so over-matching is the safe direction. Exact token match, so a reader
# named get_updates is not mistaken for a writer named update.
MUTATING_VERBS = {
    "write", "create", "update", "patch", "delete", "move", "rename",
    "append", "insert", "upsert", "remove", "edit", "add", "set", "put",
    "post", "replace", "modify", "manage", "duplicate", "archive",
}

# Add tool names your setup uses that the verb test misses, one per line, in
# ~/.claude/precision/write-tools.txt. Nothing needs to be listed for the common
# cases; this is the escape hatch for a tool with an idiosyncratic name.
EXTRA_WRITE_TOOLS = os.path.join(PRECISION_DIR, "write-tools.txt")


def is_mcp_write(tool):
    if not tool.startswith("mcp__"):
        return False
    try:
        with open(EXTRA_WRITE_TOOLS, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and line == tool:
                    return True
    except OSError:
        pass
    tail = tool.split("__")[-1]
    return any(t in MUTATING_VERBS for t in re.split(r"[^a-z]+", tail.lower()) if t)


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def under_guarded(path, roots):
    # normcase and normpath so this works where the separator is a backslash and
    # the filesystem is case-insensitive, rather than only on unix.
    def norm(x):
        return os.path.normcase(os.path.normpath(nfc(x)))
    p = norm(path)
    for root in roots:
        r = norm(root)
        if p == r or p.startswith(r + os.sep):
            return True
    return False


def unconfigured_notice(session):
    """Say once per interval that the gate has nowhere to guard.

    Same contract as every other check in this set: not configured is reported,
    never passed off as nothing found.
    """
    marker = os.path.join(TMP, "claude-hook-notice-" + hashlib.md5(
        ("guarded-roots-unset|" + session).encode()).hexdigest())
    try:
        if time.time() - os.path.getmtime(marker) < PROBE_INTERVAL:
            return
    except OSError:
        pass
    try:
        open(marker, "w").close()
    except Exception:
        pass
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            "SENSEMAKING GATE NOT RUNNING: no paths in " + GUARDED_ROOTS_FILE +
            ", so it is guarding nothing. Put one absolute path per line there, "
            "naming where your material lives. Until then this hook is installed "
            "and inert."
        ),
    }}))
    sys.exit(0)


def ask(extra=""):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": REASON + (("\n\n" + extra) if extra else ""),
    }}))
    sys.exit(0)


def paused_for(path):
    """Remaining minutes if a live, in-scope pause covers this path, else None."""
    try:
        age = time.time() - os.path.getmtime(PAUSE)
        with open(PAUSE, encoding="utf-8") as fh:
            lines = [l.strip() for l in fh]
    except OSError:
        return None
    minutes = DEFAULT_PAUSE_MINUTES
    prefixes = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        found = re.match(r"minutes:\s*(\d+)\s*$", line, re.IGNORECASE)
        if found:
            minutes = int(found.group(1))
        else:
            prefixes.append(line)
    if minutes <= 0 or age > minutes * 60:
        return None
    p = nfc(path)
    for x in prefixes:
        if p.startswith(nfc(x)):
            return int((minutes * 60 - age) / 60)
    return None


def stood_down(left, extra=""):
    msg = ("Sensemaking gate paused for this path by " + PAUSE + ", about " +
           str(left) + " minutes remaining. Scoped to the listed prefixes only, "
           "and it expires on its own. Delete the marker to end it now.")
    # A pause covers the sensemaking prompt and nothing else. An exposure
    # warning is a live leak rather than a question, so it is never stood down.
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": msg + (("\n\n" + extra) if extra else ""),
    }}))
    sys.exit(0)


def precision_warning(session):
    """Return a warning if anything in the precision directory is exposed to git.

    This gate cannot print a second JSON object, since its channel carries a
    permission decision, so the warning is returned and folded into whichever
    single object this run produces. One probe per interval, and the marker key
    names the check rather than the hook, so whichever hook runs first does the
    work and the rest skip it until the interval is up.

    Every file in the directory is checked rather than a named one, because a
    check that resolves a single filename reports as though it covered the
    directory while covering one file in it.
    """
    if not os.path.isdir(PRECISION_DIR):
        return ""
    marker = os.path.join(TMP, "claude-hook-notice-" + hashlib.md5(
        ("inbox-exposure|" + session).encode()).hexdigest())
    try:
        if time.time() - os.path.getmtime(marker) < PROBE_INTERVAL:
            return ""
    except OSError:
        pass  # no marker yet, so this is the first probe of the session
    d = PRECISION_DIR

    def git(*args):
        return subprocess.run(("git", "-C", d) + args, capture_output=True,
                              text=True, timeout=5).returncode

    exposed = []
    try:
        if git("rev-parse", "--is-inside-work-tree") != 0:
            return ""
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
        return ""
    try:
        open(marker, "w").close()
    except Exception:
        pass
    if exposed:
        return ("PRECISION MATERIAL EXPOSED in " + d + ": " +
                "; ".join(n + " is " + why for n, why in exposed) +
                ". Anything tracked is already published, and 'git rm --cached' "
                "does not unpublish it. Anything unignored is one 'git add -A' "
                "from the same place.")
    return ""


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as err:
        # A gate that cannot read its input does not know whether this write is
        # guarded, and silently allowing it is the failure this hook exists to
        # prevent. Ask instead, naming the reason. "ask" still never hard-blocks.
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                "Sensemaking gate could not read its input (" +
                type(err).__name__ + ": " + str(err) + "), so it cannot tell "
                "whether this path is guarded. Approve only if you know it is not."
            ),
        }}))
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    warning = precision_warning(data.get("session_id", "nosess") or "nosess")
    if is_mcp_write(tool):
        ask(warning)
    if tool in FILE_TOOLS:
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        roots = guarded_roots()
        if not roots:
            unconfigured_notice(data.get("session_id", "nosess") or "nosess")
        if under_guarded(path, roots):
            left = paused_for(path)
            if left is not None:
                stood_down(left, warning)
            ask(warning)
    # Not a guarded path, so no decision is owed. The warning still has to reach
    # someone, and with no decision in the object it can travel as context.
    if warning:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": warning,
        }}))
    sys.exit(0)


if __name__ == "__main__":
    main()
