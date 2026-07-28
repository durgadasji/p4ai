#!/usr/bin/env python3
"""Draw the setup panel, from what is on disk rather than from what was said.

The setup skill prints this before each question. It is a script rather than
something the model composes because the panel makes claims about which files
exist, and a claim the model assembles from memory of its own earlier turns is
exactly the kind this package refuses everywhere else. Every line below is read
from the directory at the moment it prints.

It is also the answer to a smaller problem: an interview that stops halfway
leaves no trace. The marker file this reads outlives the session, so the next
one opens knowing there is an unfinished install and where it stopped.

Usage:
    setup-panel.py            draw the panel
    setup-panel.py --begin N  write the marker, at question N
    setup-panel.py --end      remove the marker, setup finished
"""

import os
import sys
import json
import time

PRECISION_DIR = os.environ.get("PRECISION_DIR") or os.path.expanduser(
    "~/.claude/precision")

MARKER = os.path.join(PRECISION_DIR, "setup-in-progress")

# The questions, in the order the skill asks them, paired with the file each
# one writes. Order matters here: it is what makes "3 of 5" mean anything, and
# it has to match the skill or the panel will lie about position.
ASKED = [
    ("guarded-roots.txt", "where your material lives"),
    ("house-style.txt", "writing rules"),
    ("terms.txt", "what must never be published"),
    ("working-prefix.txt", "what marks working documents"),
    ("public-repos.txt", "repositories safe to name"),
]

# Raised only if wanted. They are listed so their absence reads as a decision
# not yet made rather than as something missing, which is the same reason every
# check in this package names what it is not checking.
OPTIONAL = [
    ("exempt.txt", "published vocabulary that collides with your terms"),
    ("canon-patterns.json", "facts that must not drift"),
    ("vocabulary-scope.txt", "where the vocabulary gate applies"),
    ("term-registry.json", "the terms it checks against"),
    ("write-tools.txt", "MCP tools that write without saying so"),
]

WIDTH = 64


def entries(name):
    """Count meaningful lines, or None if the file is not there.

    Comments and blanks do not count, because a file holding nothing but the
    comments it shipped with is unconfigured however many bytes it has.
    """
    path = os.path.join(PRECISION_DIR, name)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            if name.endswith(".json"):
                data = json.load(fh)
                return len(data) if hasattr(data, "__len__") else 1
            return sum(1 for line in fh
                       if line.strip() and not line.lstrip().startswith("#"))
    except (OSError, ValueError):
        return "unreadable"


def marker():
    """Current question number, or None when no setup is in progress."""
    try:
        with open(MARKER, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("question:"):
                    return int(line.split(":", 1)[1].strip())
    except (OSError, ValueError):
        pass
    return None


def row(label, name, detail, count):
    if count is None:
        state = "."
    elif count == "unreadable":
        state = "unreadable"
    elif isinstance(count, int):
        state = "%d %s" % (count, "entry" if count == 1 else "entries")
    else:
        state = str(count)
    line = "  %-16s %-26s %s" % (label, name, state)
    return "|" + line.ljust(WIDTH - 2)[:WIDTH - 2] + "|"


def draw():
    at = marker()
    header = " pt4ai setup "
    if at:
        header += "".ljust(WIDTH - len(header) - 12, "-") + " %d of %d " % (
            at, len(ASKED))
    out = ["+" + header.ljust(WIDTH - 2, "-")[:WIDTH - 2] + "+"]

    written = [(n, d) for n, d in ASKED if entries(n) is not None]
    pending = [(n, d) for n, d in ASKED if entries(n) is None]

    if written:
        first = True
        for name, detail in written:
            out.append(row("WRITTEN" if first else "", name, detail,
                           entries(name)))
            first = False
    if pending:
        out.append("|" + " " * (WIDTH - 2) + "|")
        first = True
        for name, detail in pending:
            out.append(row("PENDING" if first else "", name, detail, None))
            first = False

    opt = [(n, d) for n, d in OPTIONAL]
    if opt:
        out.append("|" + " " * (WIDTH - 2) + "|")
        first = True
        for name, detail in opt:
            count = entries(name)
            out.append(row("OPTIONAL" if first else "", name, detail,
                           count if count is not None else "not asked"))
            first = False

    out.append("+" + "-" * (WIDTH - 2) + "+")
    return "\n".join(out)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--begin":
        n = args[1] if len(args) > 1 else "1"
        os.makedirs(PRECISION_DIR, exist_ok=True)
        with open(MARKER, "w", encoding="utf-8") as fh:
            fh.write("# pt4ai setup is in progress. Written when the interview\n"
                     "# starts and removed when it finishes, so an interview\n"
                     "# abandoned halfway says so instead of vanishing.\n"
                     "# Delete this by hand to stop it being reported.\n")
            fh.write("question: %s\n" % n)
            fh.write("started: %s\n" % time.strftime("%Y-%m-%d %H:%M"))
        return
    if args and args[0] == "--end":
        try:
            os.remove(MARKER)
        except OSError:
            pass
        return
    print(draw())


if __name__ == "__main__":
    main()
