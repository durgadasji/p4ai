# Provenance

Where this package's claims come from, which versions it read, and which of its files actually act. Not a standard, and not a list of the standards: a declaration about this package.

## The servers are instruments. The standards are the authority.

This distinction is the one most worth holding, because the two are easy to confuse and the confusion is expensive.

A standard is normative. It says what is required, it carries its own changelog, and it is public at a URL you can read. A server is a convenience that answers questions about a standard quickly. It can be stale, it can be incomplete, and it can be wrong, and none of those states announces itself in the answer.

That is not hypothetical. A server bundle can sit two minor releases behind while answering with the confidence of something current, and hand out links to filenames that no longer exist, because the filenames carry versions and the versions moved.

So three habits, in order of how much they cost you.

Read the `_provenance` block. Every server response declares which versions produced it. It costs nothing and it converts an invisible staleness into a visible one.

When a claim is load-bearing, read the standard at its source rather than asking the instrument. The server gives you pointers and checklists; the standard is the thing that can settle a question. This package's own first rule says a secondary record inherits whatever was true when it was written, and a server is a secondary record.

Treat a surprising answer as a question about the instrument before treating it as a finding about your work. If a server disagrees with a standard you have read, the server is the more likely to be wrong.

The published names keep this visible. Three packages are instruments you run: `@proof-of-coord/structural-integrity`, `@proof-of-coord/evidence-integrity` and `@proof-of-coord/frame-language`. A fourth, `@proof-of-coord/evidence-core`, is a library the evidence instrument depends on rather than a server. The standards they serve live elsewhere, under their own names, at their own versions, and a server's version tells you nothing about which version of a standard it carries.

## What it does not claim

This plugin does not claim conformance at any adoption tier. The Sensemaking Standard's inheritance clause commits an adopting system to naming its practices against the invariants, assessing sensemaking capacity at three scales, and treating sensemaking failures as coordination events requiring documented review. Those commitments are for a coordination system with participants. This is a tool one person installs, so claiming a tier would be borrowing the credibility of a conformance process that never ran.

What it does instead is narrower and checkable: it cites specific invariants where its behaviour depends on them, and names the version it read.

## Two different things, kept apart

**What this plugin's own text asserts against.** Two standards, cited by invariant where behaviour depends on them.

| Standard | Version read | Where it is load-bearing |
|---|---|---|
| Sensemaking Standard (SMS) | 1.1.23 | `hooks/sensemaking-gate.py` builds its prompt from Invariants 3.1, 3.4 and 3.5 and the witness-reception scale (2.3, 4.3). The gate asks whether a frame changed rather than whether thinking is complete, because 3.3 names a rule barring the write until understanding is complete as analysis paralysis, and 3.4 puts the terminal state at sufficiency. `method/working-discipline.md` cites 3.1, 3.3, 3.4 and Section 9.6. |
| Precision-First Design Standard (PFDS) | 2.4.3 | `rules/pt4ai.md` and `method/working-discipline.md` treat precision and non-harming as one commitment with two constitutive aspects rather than two principles in tension, per Section 2. The two failure directions, under-correction and over-correction, follow from the invariant. |

**What the servers carry.** Five separate bodies of work, about five different subjects. Installing the servers puts all of them on your machine at the versions pinned when you installed, whether or not this plugin's text ever cites them. Every server response declares which versions produced it, which is how you tell what you have.

| Body | What it is about | Exposed as |
|---|---|---|
| Coordination Structural Integrity Suite | Structural conditions for coordination: ten standards, listed below | `csis` server |
| Dimensional Frame Language | The language coordination is described in, and a watchlist of terms that conceal structure | `frame-language` server, term registry |
| CROSS | Conformance of a funding or grant transaction between applicant and funder | `cross_*` tools |
| WALKRI | Quality of a field instrument itself | `walkri_*` tools |
| ORE | Grading a source by origin, reliability and exposure, as uncertainty rather than quality | `ore_*` tools |

CROSS and WALKRI share one encoded foundation, `cross-walkri-primitives-foundation`, and the server also carries a finding contract alongside ORE. All are declared in its `_provenance`.

The last three share one server and are not one thing. They answer different questions and can be right or wrong independently.

The ten standards inside the first row:

| Standard | Version |
|---|---|
| Precision-First Design Standard | 2.4.3 |
| Adverse-Signal Engagement Principle Core Standard | 0.7.13 |
| Coordination Scaling Standard | 0.1.5 |
| Information Asymmetry Classification Standard | 0.1.26 |
| Regenerative Obligation Standard | 0.1.8 |
| Structural Consent Legibility Standard | 0.3.25 |
| Structural Power Obligation Standard | 0.1.26 |
| Conflict Transformation Standard | 0.2.10 |
| Four Batteries Capacity Standard | 0.3.7 |
| Sensemaking Standard | 1.1.23 |

All are public. Read them rather than trusting this table: a secondary record inherits whatever was true when it was written, which is the first rule in this package.

```json
{
  "asserted_against": [
    { "id": "sms",  "version": "1.1.23" },
    { "id": "pfds", "version": "2.4.3" }
  ],
  "carried_by_servers": {
    "csis-suite": "pfds@2.4.3, asep@0.7.13, css@0.1.5, iacs@0.1.26, ros@0.1.8, scls@0.3.25, spos@0.1.26, cts@0.2.10, fbcs@0.3.7, sms@1.1.23",
    "frame-language": "term-registry@0.1.0",
    "evidence-integrity-suite@0.4.0": "cross-walkri-primitives-foundation@0.2.3, ore@0.1.2, finding-contract@0.1.0"
  }
}
```

That block is what a currency check reads. Every server declares its versions the same way, in a `_provenance` field required on every response, so one mechanism reads all of them. The lists still move independently: this plugin can cite a version the servers no longer carry, the servers carry standards this plugin never mentions, and the bodies version on separate clocks.

## Which files actually run

Effective. These execute and can change what happens to your work:

- `hooks/hooks.json` and the five hooks it wires: `sensemaking-gate.py`, `style-check.py`, `canon-check.py`, `hook-once.py`, and `vocabulary-check.py`, which is present but deliberately not wired.
- `scripts/`: `residue-scan.template.sh`, `private-reference-check.sh`, `link-check.sh`, `check-prerequisites.py`. Run by hand or from continuous integration.

Read only. These are text that shapes behaviour through context, not code:

- `rules/pt4ai.md`, loaded every session if you install it into your rules directory.
- `skills/precision-mode/SKILL.md`, loaded when the skill is invoked.
- `method/working-discipline.md` and `README.md`, read by you.

The distinction matters because the prose can be ignored under pressure and the executables cannot. If you are auditing this before installing, the executables are the part that will act on your machine whatever anyone intends.

## Keeping this honest

This file is maintained by hand and will go stale exactly like any other secondary record. It belongs in the publishing checklist rather than in anyone's memory, alongside the changelog. Two things make it detectable when it lapses: the version block above, and the standards' own changelogs, which record what changed between any two versions named here.
