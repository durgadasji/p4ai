#!/usr/bin/env python3
"""Regression fixtures: prove each check fails on a case known to be bad.

A check that has never failed has not been tested. Every case below is drawn
from a real failure that survived multiple edit sessions in a working corpus,
reduced to the smallest input that reproduces it, so the fixture carries the
shape of the failure and none of the material it was found in.

Each case runs twice and both directions have to hold. The bad input must be
flagged, because a check that cannot fail is decoration. The clean input must
not be, because a check that fires on everything is worse than none: it teaches
the person to stop reading it, and then the one that mattered scrolls past.

Python rather than bash on purpose. The pre-publish gates are shell and do not
run on Windows without help; the thing that proves the hooks work should run
wherever the hooks do.

    python3 tests/run.py          run them
    python3 tests/run.py -v       show each hook's actual output
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)

# Each case names the hook it exercises, the configuration that arms it, the
# input that must be caught, the input that must not be, and a fragment of the
# message that proves the right rule fired rather than some other complaint.
CASES = [
    {
        "name": "canon: version drift",
        "found": "A document citing a protocol at v3.2.0 while the corpus held "
                 "v3.8.0. Survived review because the citation was correctly "
                 "formatted and only the number was stale.",
        "hook": "hooks/canon-check.py",
        "config": {
            "canon-patterns.json": json.dumps({
                "scope": ["/guarded/"],
                "exempt": [],
                "rules": [{
                    "id": "protocol-version",
                    "pattern": r"protocol\s+v?3\.(?!8\.0)\d+\.\d+",
                    "message": "the protocol is at v3.8.0; this cites an "
                               "earlier version",
                }],
            }, indent=2),
        },
        "bad": "The ingestion path is specified in protocol v3.2.0, section 4.\n",
        "clean": "The ingestion path is specified in protocol v3.8.0, section 4.\n",
        "expect": "v3.8.0",
    },
    {
        "name": "vocabulary: retired term still in use",
        "found": "A term retired by a naming decision, still present in two "
                 "places in a specification months later. Nothing flagged it "
                 "because the replacement was adopted everywhere else and the "
                 "document read as current.",
        "hook": "hooks/vocabulary-check.py",
        "config": {
            "term-registry.json": json.dumps({
                "version": "0.0.0-fixture",
                "terms": [{
                    "term": "governance surface",
                    "note": "retired; use the replacement named in the decision",
                }],
            }, indent=2),
            "vocabulary-scope.txt": "/guarded/\n",
        },
        "bad": "Proposals are adopted at the governance surface after review.\n",
        "clean": "Proposals are adopted at the deliberate coordination surface "
                 "after review.\n",
        "expect": "governance surface",
    },
]


def run_hook(hook, precision_dir, target, session):
    """Feed a hook the payload Claude Code feeds it, return what it printed."""
    payload = json.dumps({
        "session_id": session,
        "tool_input": {"file_path": target},
    })
    env = dict(os.environ)
    env["PRECISION_DIR"] = precision_dir
    # Notices dedupe per session against markers in the temp directory. A fresh
    # one per run keeps a previous run from silencing this one, which would read
    # as a pass.
    env["TMPDIR"] = os.path.join(precision_dir, "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)
    proc = subprocess.run(
        [sys.executable, os.path.join(PLUGIN, hook)],
        input=payload, capture_output=True, text=True, env=env)
    return proc.stdout.strip()


def context_of(out):
    """The message text a hook emitted, or empty when it said nothing."""
    if not out:
        return ""
    try:
        return json.loads(out).get(
            "hookSpecificOutput", {}).get("additionalContext", "")
    except ValueError:
        return out


def main():
    verbose = "-v" in sys.argv
    failures = []
    for i, case in enumerate(CASES):
        root = tempfile.mkdtemp(prefix="pt4ai-fixture-")
        try:
            precision = os.path.join(root, "precision")
            guarded = os.path.join(root, "guarded")
            os.makedirs(precision)
            os.makedirs(guarded)
            for name, body in case["config"].items():
                with open(os.path.join(precision, name), "w",
                          encoding="utf-8") as fh:
                    fh.write(body)

            results = {}
            for kind in ("bad", "clean"):
                target = os.path.join(guarded, kind + ".md")
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write(case[kind])
                results[kind] = context_of(run_hook(
                    case["hook"], precision, target,
                    "fixture-%d-%s" % (i, kind)))

            caught = case["expect"] in results["bad"]
            quiet = case["expect"] not in results["clean"]

            if caught and quiet:
                print("  PASS  %s" % case["name"])
            else:
                print("  FAIL  %s" % case["name"])
                if not caught:
                    print("        bad input was not flagged")
                if not quiet:
                    print("        clean input was flagged")
                failures.append(case["name"])

            if verbose:
                for kind in ("bad", "clean"):
                    print("        [%s] %s" % (
                        kind, results[kind].replace("\n", " ")[:160] or
                        "(said nothing)"))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    print()
    if failures:
        print("  %d of %d failed. A check that does not catch its own "
              "documented case is not protecting anything." % (
                  len(failures), len(CASES)))
        return 1
    print("  %d of %d passed, in both directions." % (len(CASES), len(CASES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
