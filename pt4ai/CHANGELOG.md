# Changelog

Versions follow the `version` field in `.claude-plugin/plugin.json`. A user receives an update only when that field moves, so every entry here corresponds to a bump.

Read this before accepting an update. Changes to the hooks alter what fires on your writes, and changes to the referenced standards alter what the gates assert about your work, which is closer to accepting a dependency bump than to taking a bug fix.

## 0.1.0

First release. Not yet published.

**Layers.** Five, each acting at a different moment: always-on rules at intention, the `precision-mode` skill at approach, hooks at write time, gates at publish time, and the standards servers as callable instruments. The servers are declared but not yet available, since their packages are unpublished.

**What the hooks do.** `sensemaking-gate.py` asks for confirmation before writes to paths you nominate, using the Sensemaking Standard's own tests rather than a completeness question. `style-check.py`, `canon-check.py` and `vocabulary-check.py` check written files against your own house style, a facts-that-must-not-drift pattern file, and a published term registry. No writing rules ship as defaults. `hook-once.py` restates standing obligations, one of which repeats deliberately rather than deduplicating.

**The contract every check holds.** A check that cannot run says so. None of them reports a clean result it did not earn: an unset path, a missing configuration file, an unreadable target and a malformed pattern each produce a notice naming what is not being checked. None of them blocks a write.

**Privacy.** Nothing about your work leaves the machine. The hooks and the gates make no network calls. Your terms, paths and designations live in `~/.claude/precision/`, which ships with a deny-by-default ignore rule, and both the gates and the hooks verify that rule rather than trusting it, checking whether git already tracks a file before checking whether it is ignored.

**Configuration.** Nothing is assumed about your filing. Guarded roots, private terms, exemptions, extra write tools and publicly nameable repositories are all files you write, and every check that depends on one announces itself as unarmed until you do.

**Standards referenced.** This plugin's own text asserts against two: Sensemaking Standard 1.1.23 and Precision-First Design Standard 2.4.3. The servers, when they land, carry the whole ten-standard suite regardless of what the text cites. `PROVENANCE.md` keeps those two lists apart, since they move independently.

**Known gaps at this version.** The standards servers are unavailable pending package publication. The three shell gates require bash and so do not run on Windows without WSL or git-bash. `/pt4ai:setup` conducts the first-run configuration, and until it is run every check will correctly report itself unconfigured rather than reporting clean.
