# Precision method for Claude Code

An operating discipline for building precise things with a model, packaged so it runs rather than sits in a file you meant to reread. It came out of a corpus of coordination and evidence standards, but nothing in it is domain-specific.

## Five layers, and why there are five

Each layer acts at a different moment, and each catches a class of failure the others structurally cannot. That is the whole design. A single clever rule fails because it acts at one moment and leaves the others uncovered.

**Intention. Always on.** `rules/pt4ai.md` loads at the start of every session: read the source before asserting it, verify before claiming, agreeing with you is not a service, and every disconfirmation pairs with a move. Rules are context, not enforcement, so this layer is the one that gets ignored under pressure. That is why the others exist. Remove the file to turn it off.

**Approach. On demand.** The `precision-mode` skill, invoked when the work turns structural. It changes what happens first, what gets refused, and what gets checked before anything is asserted. Never invoke it and it never loads.

**Write time. Automatic.** The hooks fire on every write whether anyone remembers them or not, catching what the rules failed to hold on a long day. They are also the layer that reports what it is *not* checking, so an unconfigured gate says so instead of reporting clean. Remove an entry from `hooks/hooks.json` to turn one off.

**Publish time. On demand.** The gates in `scripts/` run before anything leaves your machine, catching what accumulated while nobody was looking: private references, dead links, material that should not travel. Run them or do not.

**Instruments. Callable.** The standards servers, exposing the definitions and checklists the discipline points at, so a claim about a standard can be resolved rather than remembered. They run locally on your machine, not as a service anyone hosts. Do not install them and the other four layers work unchanged; the checks that name a standard simply cannot resolve it for you.

The servers are instruments; the standards are the authority. A server answers quickly and can be stale, incomplete or wrong without saying so, while the standard is normative, public, and carries its own changelog. `PROVENANCE.md` states which standards this package asserts against, which bodies of work the servers carry, and which files here actually execute rather than being prose.

Those servers carry the standards inside them, pinned at the version you installed. When a standard is revised upstream, your copy does not change and nothing tells you. This is not hypothetical: a stale bundle will happily report version numbers two minor releases behind while answering with the confidence of something current, and hand out links to filenames that no longer exist. Every response declares which versions produced it, so the way to catch it is to read that declaration rather than trust the answer. Update deliberately, the same way you would any dependency.

Turning a layer off is expected and supported. Every check that is present but unconfigured says so once per session, so an unarmed check cannot pass for a working one. A layer you remove outright goes quiet along with it, because a check that is not running cannot report that it is not running. That is the one case worth writing down somewhere you will read it again.

## What it does not do

Nothing about your work leaves your machine, ever. The hooks make no network calls at all, and neither do the gates that read your material.

Two connections exist and both are ordinary. Installing the standards servers downloads them once from the public package registry, the way any dependency install does, after which they run locally and offline. And the link checker contacts the URLs written in your own files, because that is what checking a link is; you run it by hand. Your terms, your paths and your private designations stay in `~/.claude/precision/`, which ships with a deny-by-default ignore rule so they cannot reach a commit.

It will also disagree with you more than you are used to, decline to tell you whether an idea is good, and report what it did not check. That is the product, not a malfunction.

## What it costs to set up

Be clear-eyed about this before you start. This is not a plugin you install and use; it is one you configure and then use. Ten files decide what it checks, and it ships with none of them written, because every one of them encodes a judgment that is yours: where your material lives, what counts as private, what your house style is, which repositories you may name.

That is the deliberate trade. A package with defaults would work in ten minutes and would be checking someone else's answers against your work, silently, forever. This one checks nothing until you say what to check, and tells you so every session until you do.

Expect twenty minutes for the parts that matter and a slow accretion after that, which is the honest pattern: a denylist grows an entry each time something nearly leaks, so a list finished in one sitting is a list that was guessed.

In order of what buys the most first: `guarded-roots.txt` so the gate knows what to protect, `house-style.txt` so writing is checked at all, then `terms.txt` before your first publish. The rest can wait until you meet the thing they are for.

Only one standing obligation is wired by default, the read-first reminder, because it is general. Two others ship unwired: a three-reader standard for documents and a version-bump-and-changelog reminder. Both are one author's practice, so they are yours to add if they match how you work.

## Install

Two commands, then a conversation.

```
/plugin marketplace add durgadasji/p4ai
/plugin install pt4ai@p4ai
```

Installing delivers the hooks, both skills and the manifest. Nothing to copy, no
`settings.json` to edit: `hooks/hooks.json` wires the hooks for you, and they are
removed just as cleanly when you uninstall.

Run the setup, which is the actual install:

```
/pt4ai:setup
```

It checks your prerequisites, tells you where to get anything missing, and then
asks what to check rather than assuming it. Where your material lives, which
writing rules you want, what must never be published. It writes the answers into
`~/.claude/precision/` and finishes by proving the thing works: a deliberate
violation in a guarded file, so you watch the gate ask and the checker report
before you trust either. Invoke it again any time to change an answer.

### The one manual step

Copy `rules/pt4ai.md` to `~/.claude/rules/pt4ai.md`.

A plugin cannot write into your rules directory, and that is the right
restriction rather than a limitation: those rules load into every session in
every project, and something that installs itself into every conversation you
have should be a thing you put there deliberately.

Anything in `~/.claude/rules/` loads at the start of every session, so this is
always on without editing a file you already own. It is deliberately not named
`CLAUDE.md`, because dropping a file with that name into your home directory
would overwrite instructions you have written, and a package that quietly
replaces your own rules has done something worse than failing to install. If you
would rather keep it inside your own `CLAUDE.md`, add one line there instead:
`@~/.claude/rules/pt4ai.md`.

Read it before you install it and cut what does not fit.

### The gates

`scripts/` holds the pre-publish checks. They run by hand or from continuous
integration rather than automatically, because deciding that something is ready
to leave your machine is not a decision to automate.

```
python3 scripts/check-prerequisites.py
bash scripts/residue-scan.template.sh <path>
bash scripts/link-check.sh <path>
```

The prerequisite check runs anywhere. The other two need bash, so on Windows they
want WSL or git-bash; the hooks and the skills do not.

`tests/run.py` proves two of the checks catch a case known to be bad, and stay
quiet on a clean one. Run it after changing a hook:

```
python3 tests/run.py
```

Each fixture came from a failure that survived several edit sessions in a real
corpus. A check that has never failed has not been tested, and one that fires on
everything is worse than none, so both directions are asserted.

### The standards servers

Optional, and the other four layers run unchanged without them. They are
published on JSR as TypeScript source, so Deno starts them and no build step or
global install is involved:

```
deno run -A jsr:@proof-of-coord/structural-integrity
deno run -A jsr:@proof-of-coord/evidence-integrity
deno run -A jsr:@proof-of-coord/frame-language
```

Each speaks the Model Context Protocol over stdio, so register the same command
with your client. In Claude Code that means a server entry whose command is
`deno` and whose arguments are `run`, `-A`, and the `jsr:` specifier.

Deno declines dependencies published within the last 24 hours. If you install
one of these the same day it is released, add `--minimum-dependency-age=0` or
wait a day. `@proof-of-coord/evidence-core` is a library the evidence server
depends on rather than a server you run.

### Removing it

Uninstalling the plugin takes back everything it installed. Two
things it does not touch, because they are yours: `~/.claude/rules/pt4ai.md`, and
`~/.claude/precision/`, which holds your answers. Delete those by hand if you
want them gone, and read the second one first.

## What each piece is for

`hooks/style-check.py` checks written files against the rules in your `house-style.txt`. The package ships none of its own: a writing rule is a taste decision, and this hook fires on every write, so it is the most visible place to impose one author's preferences on someone else. `/pt4ai:setup` walks you through `house-style.example.txt` so you keep what you agree with and nothing else.

`hooks/vocabulary-check.py` flags terms from a registry you point it at, so a vocabulary discipline is checked rather than intended. If you run the Frame Language MCP server, its term registry is the obvious source and `check_watchlist` is the same discipline on demand.

`hooks/canon-check.py` checks every written file against a pattern set holding facts that must not drift, dates, versions, counts, names. You supply the patterns. This is the one that catches a wrong fact propagating quietly across a corpus.

`hooks/sensemaking-gate.py` asks for confirmation before writes to the places your material lives. Name them one absolute path per line in `~/.claude/precision/guarded-roots.txt`; `~` is expanded and `#` comments are ignored, so the file reads as a list of places rather than a config format. Until it has paths the gate says it is installed and inert rather than sitting there quietly guarding nothing.

Notes reached through an MCP server count as writes too, whichever server that is. The gate decides by the verb in the tool name rather than by a list of tool names, so it covers note apps this package has never heard of and stays quiet for readers. Add anything with an idiosyncratic name to `write-tools.txt` beside the roots file. The bias is deliberately toward over-matching, and it runs opposite to the residue scan's: for a gate a false positive costs one click and a false negative is an unguarded write. It does not make writing wait for finished thinking, which is the failure it would otherwise install. It asks whether the frame being written actually changed, whether it is going down as provisional with its revision conditions, and whether the next reader will be able to tell what disruption produced it.

The gate can be paused, deliberately. The case it is for is stepping away mid-batch: pausing the prompts is not the same as pausing the work, and without a way to say that the only options are sitting there clicking or killing the hook. A gate with no way out gets deleted rather than paused, and a hook deleted on one tiring afternoon is gone for good.

Write one path prefix per line into `~/.claude/precision/gate-pause`, and writes under those prefixes stop prompting. Add a `minutes: N` line to set how long, or leave it out for forty-five. Set it to what you actually need, an hour if you are stepping out, five if you are watching a short batch land.

```
minutes: 90
/absolute/path/to/the/work/in/hand/
```

It is scoped, so the rest of your material stays guarded. It expires on its own, because an off switch that has to be remembered is the permanent state in disguise; `touch` restarts the clock and deleting the file ends it now. `minutes: 0` is refused rather than treated as forever.

The third bound is the one worth understanding before setting a long duration, because it makes a long duration safe. A pause only suppresses the prompt inside work already underway. It authorizes nothing new, so the work still stops when it is done and waits for you. Ninety minutes does not buy ninety minutes of unattended writing; it buys however long the current stretch takes, and the remaining time only matters if you come back and ask for more while the clock is still running.

Every paused write says so and counts down, so what landed without a prompt stays visible rather than implicit. Two things stay outside its reach: the Obsidian write tools, which always ask, and the exposure warning, which reports a live leak rather than asking a question.

`hooks/hook-once.py` is a lightweight reminder scheduler for standards that need restating rather than testing.

`scripts/link-check.sh` checks that every link in authored content resolves, and reports rate-limited hosts separately from broken ones. Scoped to authored files: an earlier version scanned dependencies and reported dead links inside third-party packages, which is noise.

`scripts/private-reference-check.sh` resolves every path-like reference in your material to a local checkout, reads its git remote, and fails if that repository is not public. This catches the class a keyword denylist cannot: a plain private filename in a document bound for a public repository looks like nothing.

`scripts/residue-scan.template.sh` catches private material on its way into public artifacts, and chains the private-reference check.

It ships with no categories, and that is the design rather than an omission. What counts as private, and how you divide it up, is yours to designate: put one pattern per line in `~/.claude/precision/terms.txt` and group them however you think about them, since nothing in the scan needs to know your groupings. Collisions go in `exempt.txt` beside it, for the case where a word that is private in your filing is a defined term in somebody's published specification. Both paths move with `PRECISION_TERMS` and `PRECISION_EXEMPT`.

A built-in taxonomy would fail twice over. It would hand you someone else's way of dividing your material, and it would disclose that division to anyone reading the script, because a list of what to look for is a negative image of what is being protected. Two checks are built in because they are general rather than anybody's: the em dash rule, and references matched by your working prefix.

The scan states what is armed before it states a result. With no terms file it says so and warns that a clean result means very little. With one, it reports how many terms it holds and when the list last changed, and says plainly that a list which has not moved in months is a question rather than an achievement, since a list like that grows when something nearly leaks.

Before scanning anything it verifies its own protection: that nothing in `~/.claude/precision/` is tracked by git or left uncovered by the ignore rule. It checks tracking first, because an ignore rule does not reach a file git already tracks, so a file committed before the rule existed is published no matter what the rule says now. If anything is exposed the scan refuses to run, on the grounds that the list of what you protect leaking is worse than any single thing on it.

## A caution about the checks

The dangerous failure is not a check that fails. It is a check that passes because it is checking nothing.

While building the link checker I widened a pattern to catch URL templates, put a bracket inside a character class where it closed the class early, and the expression matched nothing at all. Every repository came back clean, including one I already knew had a dead link. It only surfaced because a known-bad case had gone quiet.

So when you add or change a check, test it against something you know is broken, and confirm it still fails. A gate you have never seen fail is a gate you have no evidence about.

The hooks here are built to that rule rather than only described by it. None of them swallows a failure: an unset path, a missing or malformed configuration file, an unreadable target, a bad regex in your own pattern file, each says once per session that the check is not running and why. What they will not do is report a clean result they did not earn. If a hook has gone quiet, that is a finding about the files rather than about the hook, which is the only condition under which silence means anything.

## Where the depth is

If you are running the coordination suite and Frame Language MCP servers, the instruments behind this discipline are already callable. `lookup_three_frames` for the frame vocabulary the sequence rests on. `frame2_functioning_check` for eight named ways correct vocabulary conceals a missing structure, each with a detection variant. `lookup_corollary` for the under- and over-specification failure modes at each level. `list_standards` for the ten coordination standards.

Pull both servers if your copy predates 27 July 2026. Before that date the standard links `list_standards` returned were dead, encoded versions trailed the standards by up to two minor releases, and argument errors surfaced as raw protocol failures rather than as readable messages.

`method/working-discipline.md` is the reasoning: what each rule prevents, and the failure that produced it. Read that when a rule seems arbitrary. It usually is not, and the reason is usually a specific way of being wrong that felt like being right.
