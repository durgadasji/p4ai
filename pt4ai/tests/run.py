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
    {
        "name": "style: a house rule is enforced",
        "found": "The first half of the proof the setup interview runs. A rule "
                 "the person chose has to be reported when their own writing "
                 "breaks it, or the rule is decoration.",
        "hook": "hooks/style-check.py",
        "config": {
            "house-style.txt": "# one regex per line\n\\bvery unique\\b\n",
        },
        "bad": "This construct is very unique among the alternatives.\n",
        "clean": "This construct is unusual among the alternatives.\n",
        "expect": "very unique",
    },
    {
        "name": "gate: asks before a write into a guarded root",
        "found": "The other half of that proof, and the only layer that stops "
                 "something. Location decides it, so both files carry the same "
                 "text and differ only in where they sit.",
        "hook": "hooks/sensemaking-gate.py",
        "config": {
            "guarded-roots.txt": "__GUARDED__\n",
        },
        "bad": "A paragraph of ordinary prose.\n",
        "clean": "A paragraph of ordinary prose.\n",
        "clean_outside": True,
        "expect": "ask",
    },
    {
        "name": "read-first fires on every write",
        "found": "The one obligation wired by default. It is deliberately not "
                 "scoped to any path and deliberately does not dedupe, so the "
                 "test is that it speaks for a file with nothing special about "
                 "it at all.",
        "hook": "hooks/hook-once.py",
        "args": ["readfirst"],
        "config": {},
        "bad": "Nothing notable here.\n",
        "clean": None,
        "expect": "read the actual source",
    },
]


def run_hook(hook, precision_dir, target, session, tool="Write", args=None):
    """Feed a hook the payload Claude Code feeds it, return what it printed.

    tool_name matters to the gate, which only guards the tools that write, and
    is ignored by the rest. Sending it always keeps the payload honest to what
    the harness actually delivers.
    """
    payload = json.dumps({
        "session_id": session,
        "tool_name": tool,
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
        [sys.executable, os.path.join(PLUGIN, hook)] + list(args or []),
        input=payload, capture_output=True, text=True, env=env)
    return proc.stdout.strip()


def context_of(out):
    """Everything a hook said, flattened.

    Write-time hooks answer with additionalContext. The gate answers a
    PreToolUse call with a permission decision instead, so both are folded into
    one string: a fixture asserts on what the person would actually see, not on
    which field carried it.
    """
    if not out:
        return ""
    try:
        block = json.loads(out).get("hookSpecificOutput", {})
    except ValueError:
        return out
    return " ".join(str(block.get(k, "")) for k in (
        "permissionDecision", "permissionDecisionReason", "additionalContext"))


def main():
    verbose = "-v" in sys.argv
    failures = []
    for i, case in enumerate(CASES):
        root = tempfile.mkdtemp(prefix="pt4ai-fixture-")
        try:
            precision = os.path.join(root, "precision")
            guarded = os.path.join(root, "guarded")
            elsewhere = os.path.join(root, "elsewhere")
            for d in (precision, guarded, elsewhere):
                os.makedirs(d)
            for name, body in case["config"].items():
                # A guarded root is an absolute path and the temporary one is
                # only known now, so the case writes a sentinel and it is filled
                # in here. Plain substitution rather than str.format, because
                # half these bodies are JSON and are full of braces.
                with open(os.path.join(precision, name), "w",
                          encoding="utf-8") as fh:
                    fh.write(body.replace("__GUARDED__", guarded))

            results = {}
            # A case may have no clean direction. read-first is the deliberate
            # instance: it is scoped to nothing and fires on every write by
            # design, so an input it stays quiet for would be the defect.
            kinds = ("bad",) if case.get("clean") is None else ("bad", "clean")
            for kind in kinds:
                # Some cases turn on location rather than content: the gate asks
                # about a file because of where it is. Those put the clean file
                # outside the guarded root and keep the text identical, so the
                # only thing under test is the thing being claimed.
                where = elsewhere if (
                    kind == "clean" and case.get("clean_outside")) else guarded
                target = os.path.join(where, kind + ".md")
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write(case[kind])
                results[kind] = context_of(run_hook(
                    case["hook"], precision, target,
                    "fixture-%d-%s" % (i, kind), args=case.get("args")))

            caught = case["expect"] in results["bad"]
            quiet = ("clean" not in results
                     or case["expect"] not in results["clean"])

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
                for kind in kinds:
                    print("        [%-5s] %s" % (
                        kind, results[kind].replace("\n", " ")[:150].strip() or
                        "(said nothing)"))
                if "clean" not in results:
                    print("        [clean] none by design; see the case note")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    print()
    if failures:
        print("  %d of %d failed. A check that does not catch its own "
              "documented case is not protecting anything." % (
                  len(failures), len(CASES)))
        return 1
    both = sum(1 for c in CASES if c.get("clean") is not None)
    rest = len(CASES) - both
    print("  %d of %d passed. %d assert both directions; %d %s no clean "
          "direction by design." % (
              len(CASES), len(CASES), both, rest,
              "has" if rest == 1 else "have"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
