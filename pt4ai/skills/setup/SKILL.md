---
description: Set up the precision method by asking what to check rather than assuming it. Walks through where your material lives, what writing rules you want, and what must never be published, then writes the configuration files. Invoke after installing the plugin, or when a check reports that it is not running and you want to arm it. Also use to change an answer later.
---

# Setting this up

You are conducting an interview, not running an installer. Every answer encodes a
judgment that belongs to the person you are talking to, and the package ships
with none of them pre-filled on purpose.

Work through the questions in order. Stop at any point and write what you have;
a partly configured install is normal and every unarmed check will say so.

Before anything, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check-prerequisites.py"`
and report the result. If something is missing, give them the URL and stop there.

Write every file into `~/.claude/precision/` unless `PRECISION_DIR` is set.
Create the directory if it does not exist, and confirm that `.gitignore` is
present in it before writing anything else. That file is what keeps everything
you are about to write out of a commit. If it is missing, copy it from
`${CLAUDE_PLUGIN_ROOT}/precision/.gitignore` first and say why you did.

## Show where they are, every time

Once the prerequisites pass, mark the interview as started:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup-panel.py" --begin 1
```

Then before each question, print the panel and update the number:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup-panel.py" --begin <question number>
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup-panel.py"
```

Show its output verbatim, then ask the question underneath it. Do not describe
the panel, retype it, or summarise what it says. It reads the directory at the
moment it runs, which is the whole reason it is a script: a panel assembled from
what you remember writing could report a file that is not there, and this is a
package that refuses that everywhere else.

The marker it writes outlives the session. An interview abandoned at question
three leaves a record saying so, which is what makes a half-finished install
visible instead of silent. Remove it only at the end, and only after the proof.

## Ask these, in this order

**1. Where does your material live?**

Ask for the directories holding writing they would not want changed without
being asked: notes, drafts, a vault, a site. Absolute paths. Write one per line
to `guarded-roots.txt`.

This one first because it buys the most: until it exists the sensemaking gate
guards nothing at all.

**2. What writing rules do you want enforced?**

Show them `${CLAUDE_PLUGIN_ROOT}/house-style.example.txt` and be explicit that it is one author's
taste, not a default. Ask which rules they want and which they disagree with.
Write only what they keep to `house-style.txt`.

If they want none, say so plainly and skip it rather than writing an empty file:
a style checker with no rules is a hook that fires and finds nothing forever.

**3. What must never appear in anything you publish?**

Ask neutrally. Good phrasing: names you have claimed but are not ready to
publish, people you do not name in public, and anything you would be unhappy to
find in a public repository.

Do not offer categories. Do not suggest they might have a product line, reserved
domains, or clients under embargo. Those are one person's categories and naming
them teaches the shape of somebody else's private life rather than eliciting
theirs. Ask the open question and write what they say to `terms.txt`.

Tell them this file is the most sensitive thing in the installation, that it
never leaves their machine, and that the ignore rule beside it is what keeps it
out of a commit.

Then ask whether any of those terms are also legitimate published vocabulary
somewhere, and write those exact strings to `exempt.txt`.

**4. What marks your working documents?**

Ask whether their filing uses a prefix or folder name for drafts and working
material that should not be cited in public. Write it as a single line in
`working-prefix.txt`. If they have no such convention, say the class stays
unchecked and move on. Do not invent one for them.

**5. Which of your repositories are safe to name in public?**

Only ask if they publish. One name or slug per line to `public-repos.txt`.
Explain the direction: anything not listed is treated as undeclared, so the
check fails toward silence rather than toward exposure.

## The optional ones

Raise these only if the person seems to want them, or if they ask what else
exists. Each is genuinely optional and none of them is needed for the package to
be useful.

`canon-patterns.json` for facts that must not drift, with the format documented
at the top of `${CLAUDE_PLUGIN_ROOT}/hooks/canon-check.py`. `write-tools.txt` only
if they use an MCP tool whose name does not carry a mutating verb.

The vocabulary gate needs two things and is worth offering only to someone who
keeps a vocabulary discipline. `vocabulary-scope.txt` holds path fragments naming
the writing they want held to it, and `term-registry.json` holds the terms. The
published Dimensional Frame Language registry is one source:

```
curl -o ~/.claude/precision/term-registry.json \
  https://jsr.io/@proof-of-coord/frame-language/0.1.0/src/term-registry.json
```

Fetch it once, with them watching, and say out loud that this is the only moment
anything is downloaded: the hook itself never reaches the network. Their own
registry works just as well, and `PRECISION_REGISTRY` points at it if they keep
one elsewhere. Pin the version in that URL rather than tracking latest, because a
registry that changes underneath them changes what their writing is checked
against without saying so.

## Finish by proving it works

Do not end by saying it is configured. Show them.

What you can demonstrate depends on what they configured, so pick the largest
proof their answers support and say which one you are running.

With guarded roots and house style both set, write a file inside one of their
guarded roots containing something their own house style forbids. The gate should
ask before the write lands, and the style check should report the match
afterwards. Then delete the file.

With guarded roots but no house style, write an ordinary file into a guarded root
and delete it. That proves the gate alone, which is the layer that stops
something, and you say plainly that the style check was not exercised.

With neither, run the prerequisite check, report that nothing is armed yet, and
say that nothing could be demonstrated. Do not substitute a description of what
would have happened. An unproven install that says so is the correct outcome
here, and it is the one the next session can act on.

If a proof you did run does not behave as described, that is the finding, and it
is worth more than a successful setup: something is wired wrong and they now know
before trusting it.

## Afterwards

Print the panel one last time and clear the marker, in that order, so the final
state they see is read from disk rather than asserted:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup-panel.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup-panel.py" --end
```

Clear it even when they stopped early. A marker left behind after they chose to
stop would report an abandoned interview when what happened was a decision, and
this package does not confuse the two.

Then offer the status line, which is the one surface that does not scroll:

```
cp "${CLAUDE_PLUGIN_ROOT}/scripts/statusline-segment.sh" ~/.claude/precision/
```

Adding it means editing their own status line script or their settings, which is
outside this directory and therefore outside what setup owns. Ask before
touching either, show them the one line you would add, append to what is already
there rather than replacing it, and tell them that deleting that line is the
whole of the undo. If they decline, say nothing further about it: an offer
refused is not a thing to raise again.

Finally, tell them what is armed and what is not, by name. Anything they skipped
will announce itself once per session, which is the design rather than a nag, and
they can invoke this skill again to change any answer.
