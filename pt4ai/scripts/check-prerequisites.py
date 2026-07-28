"""Check that what this plugin needs is actually present, and say where to get it.

Run before trusting anything else here. A gate that cannot start is worse than an
absent one, because the absence is visible and the failure to start is not.

Written to run anywhere Claude Code runs, which is why it is Python rather than
shell: Windows has no bash by default, and the shell tools these checks would
otherwise reach for differ between macOS and Linux.
"""

import os
import platform
import shutil
import subprocess
import sys

PY_MIN = (3, 8)

DOCS = {
    "python": {
        "Windows": "https://www.python.org/downloads/windows/",
        "Darwin": "https://www.python.org/downloads/macos/",
        "Linux": "https://www.python.org/downloads/source/",
    },
    "deno": {
        "Windows": "https://docs.deno.com/runtime/getting_started/installation/",
        "Darwin": "https://docs.deno.com/runtime/getting_started/installation/",
        "Linux": "https://docs.deno.com/runtime/getting_started/installation/",
    },
    "git": {
        "Windows": "https://git-scm.com/download/win",
        "Darwin": "https://git-scm.com/download/mac",
        "Linux": "https://git-scm.com/download/linux",
    },
}

OS = platform.system()
ok = True
notes = []


def result(name, passed, detail, url=None, optional=False):
    """Report one prerequisite.

    Optional ones do not fail the run. They correspond to layers the package
    says out loud you can decline: the servers and the pre-publish gates both
    work that way, and a check that reported "not ready" for a layer the README
    calls optional would be contradicting the package's own promise.
    """
    global ok
    if not passed and not optional:
        ok = False
    print("  %s  %-22s %s" % ("PASS" if passed else
                              ("SKIP" if optional else "FAIL"), name, detail))
    if not passed and url:
        notes.append("    " + name + ": " + url)


print("Prerequisite check for the precision method plugin")
print("  platform: %s (%s)" % (OS, platform.machine()))
print()

# Python itself. If this script is running at all, some Python exists; what
# matters is whether the interpreter the hooks name is the one on PATH.
result("python (running)", sys.version_info >= PY_MIN,
       "%d.%d.%d, need %d.%d or later" % (sys.version_info[:3] + PY_MIN),
       DOCS["python"].get(OS))

# The hooks are invoked as `python3`. On Windows that name often does not exist
# even when Python does, which would leave every hook silently failing to start.
py3 = shutil.which("python3")
if py3:
    result("python3 on PATH", True, py3)
elif OS == "Windows":
    alt = shutil.which("python") or shutil.which("py")
    result("python3 on PATH", False,
           "not found" + (", but %s is" % alt if alt else ""),
           "https://docs.python.org/3/using/windows.html")
    notes.append("    On Windows, install from the Microsoft Store to get a")
    notes.append("    python3 command, or edit hooks/hooks.json to use `py -3`.")
else:
    result("python3 on PATH", False, "not found", DOCS["python"].get(OS))

# git is used only to check that your private material is not exposed to it.
# Without git those checks stand down, which they will say rather than imply.
git = shutil.which("git")
result("git on PATH", bool(git), git or "not found, exposure checks stand down",
       DOCS["git"].get(OS))

# Deno runs the standards servers. They publish to JSR as TypeScript source
# rather than as built binaries, so a TypeScript runtime is what starts them.
# Without it the callable instruments are absent and the other four layers run
# unchanged; the checks that name a standard simply cannot resolve it for you.
deno = shutil.which("deno")
result("deno (servers only)", bool(deno),
       deno or "not found, the standards servers will not start",
       DOCS["deno"].get(OS), optional=True)

# Claude Code itself, for the plugin commands.
claude = shutil.which("claude")
result("claude on PATH", bool(claude), claude or "not found",
       "https://code.claude.com/docs/en/quickstart")

# The shell gates are bash. On Windows they need git-bash or WSL; the hooks and
# this script do not.
bash = shutil.which("bash")
result("bash (gates only)", bool(bash),
       bash or "not found, the pre-publish gates will not run here",
       "https://git-scm.com/download/win" if OS == "Windows" else None,
       optional=True)

print()
if notes:
    print("  Where to get what is missing:")
    for n in notes:
        print(n)
    print()

print("  Nothing about your work leaves this machine. The hooks and the gates")
print("  that read your material make no network calls at all.")
print("  Two ordinary connections exist: installing the standards servers")
print("  downloads them once from the public registry, and the link checker")
print("  contacts the URLs written in your own files when you run it.")
print()
print("  RESULT: " + ("ready" if ok else "not ready, see above"))
sys.exit(0 if ok else 1)
