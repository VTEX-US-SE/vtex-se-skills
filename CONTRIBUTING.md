# Contributing

This repo follows a specific format, adapted from
[mattpocock/skills](https://github.com/mattpocock/skills) (structure, docs, ADRs, out-of-scope
log) plus per-skill versioning from [gstack](https://github.com/garrytan/gstack). Every skill
added here — by anyone on the team — follows this document. If a PR doesn't match it, that's a
review comment, not a judgment call.

## Repo layout

```
vtex-se-skills/
  AGENTS.md                  <- same content as CLAUDE.md
  CLAUDE.md                  <- same content as AGENTS.md
  CONTEXT.md                 <- VTEX-specific vocabulary
  CONTRIBUTING.md            <- this file
  README.md                  <- index + status
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  .cursor-plugin/plugin.json
  .agents/adr/                        <- structural decisions about this repo
  .out-of-scope/                      <- explicit "we won't do X, here's why"
  skills/<category>/<skill-name>/
    SKILL.md
    references/                       <- optional, supporting reference docs
  docs/<category>/<skill-name>.md     <- human-readable companion to SKILL.md
```

## Adding a skill

1. **Pick a category**: `presales/`, `governance/`, `in-progress/`, or `deprecated/`. If none
   fits, ask before inventing a new one — categories are a deliberate, small set.
2. **Folder name = skill slug**: `skills/<category>/<skill-slug>/`. Lowercase, hyphenated, matches
   `name:` in the frontmatter.
3. **`SKILL.md` frontmatter**, minimum:
   ```yaml
   ---
   name: <skill-slug>
   description: <what it does and when to use it — this is what triggers automatic invocation>
   version: <semver, e.g. 0.1.0>
   ---
   ```
   - `name` must equal the folder name.
   - `description` is what the model reads to decide whether to reach for the skill on its own.
     Write it the way you'd explain the trigger conditions to a colleague, not as marketing copy.
   - `version` is **per skill**, not per repo (see "Versioning" below).
   - Optional: `disable-model-invocation: true` if the skill should only run when explicitly
     invoked (see "User-invoked vs. model-invoked").
4. **Supporting files**: put them in `references/` next to `SKILL.md` when there's more than one
   (e.g. `references/profiling-signals.md`), or as plain sibling `.md` files when there's only
   one or two short ones (mattpocock does both, depending on how many).
5. **Companion doc**: add `docs/<category>/<skill-slug>.md` (see "The docs/ companion" below).
6. **Update the category's `README.md`** with a one-line bullet + link, same format as the
   existing entries.
7. **Update `.claude-plugin/plugin.json`**'s `skills` array explicitly — see "Plugin manifests"
   below. Don't rely on a wildcard path.

## Hard dependencies on externally-maintained skills

Sometimes a skill you're migrating depends on another skill that isn't ours to own — it's actively
maintained and distributed by someone outside this repo's process, especially if its output feeds a
production system. `solution-design`'s dependency on `vams-to-miro` (Miguel Carrera, distributed
via `#ai-committee`, whose output is ingested into Atlas's knowledge base) is the precedent: we
looked at vendoring a copy here and decided against it, precisely because it would create a second,
driftable copy of something with downstream production impact — exactly the anti-pattern described
above.

**Don't vendor it.** Document it in the dependent skill's `docs/<category>/<skill-name>.md` as an
external prerequisite: who maintains it, where to get it, and why it isn't bundled here. If the
external maintainer later wants this repo to become the canonical home for their skill, that's
their call to make, not something to default into by copying a zip.

## Versioning — deliberately not mattpocock's approach

Mattpocock versions the **whole repo** as one npm package (`package.json` + `.claude-plugin/`
manifests all share one semver, bumped together via Changesets). That fits his repo: one author,
one coherent product.

Ours doesn't fit that shape — skills here come from different authors (Diego, João, William,
Felipe, Gabriela...) evolving at different speeds through independent PRs, reviewed by Djan and
Noé. So we use **[gstack](https://github.com/garrytan/gstack)'s pattern instead**: a `version:`
field in each skill's own `SKILL.md` frontmatter, bumped independently, with none of gstack's
heavier automation (no CI-enforced version gate, no auto-generated changelog). Bump it by hand
when you materially change a skill; a typo fix doesn't need a bump.

We do **not** use `.changeset/` or a root `package.json` version for this reason. If that ever
changes (e.g. we start publishing this repo as an npm-installable package), revisit as an ADR.

## User-invoked vs. model-invoked

Mattpocock's repo splits every skill along this axis, and so should ours once we have enough
skills to make it matter:

- **Model-invoked** (default): the agent can reach for it automatically when the task matches the
  `description`. This is what most of our skills should be — `stakeholder-scout`, for instance,
  should fire on its own when a new deal appears, not only when someone remembers to type it.
- **User-invoked only**: reachable only by explicit command (`/skill-name`). Add
  `disable-model-invocation: true` to the frontmatter (Claude Code) — Codex's equivalent is
  `policy.allow_implicit_invocation: false` in that project's `agents/openai.yaml`, which lives
  outside this repo, not in the skill itself.

Category `README.md` files should split their bullet list into **User-invoked** / **Model-invoked**
sections once a category has both kinds, matching mattpocock's `engineering/README.md` and
`productivity/README.md`.

## The `docs/` companion

Every skill gets a matching `docs/<category>/<skill-slug>.md` — a human-readable page, separate
from the machine-facing `SKILL.md`. Mattpocock publishes his to a docs site (aihero.dev); we don't
need a site, just the file, in this repo, for anyone browsing or deciding whether to adopt a
skill. Sections, in this order (skip any that don't apply — don't pad):

1. **What it does** — plain-language summary, no marketing language.
2. **When to reach for it** — the trigger conditions in prose; a decision table if there are
   genuinely adjacent skills to disambiguate from (see `tdd.md` in mattpocock's repo for the
   pattern — "your situation → where to go").
3. **Prerequisites** — other skills or connectors it depends on. Say "none" if there are none;
   don't omit the section, so a reader knows it was checked.
4. **Reference files** — a table of what's in `references/`, one row each.
5. **Common questions** (optional) — only add this once a skill has actually hit a real point of
   confusion or a known limitation someone reported. Never invent hypothetical FAQs to fill the
   section.
6. **Author** — who wrote it and where the original source lives (repo, Slack thread, or
   claude.ai skill), since most of what lands here so far is a migration, not something written
   from scratch in this repo.

## Architecture decisions (`.agents/adr/`)

Use an ADR for a decision **about this repo's structure or tooling** — not about what a specific
skill does. Numbered, `000N-short-title.md`. Format: state the problem/constraint, the decision,
the invariants it creates going forward, and append dated "Update" sections when something gets
verified later rather than editing the original reasoning. See mattpocock's
`0002-ship-as-a-claude-code-plugin.md` for the shape: it documents a real constraint (Codex's
plugin manifest only accepts a single path, not an array, and drops symlinks on install) that
forced shipping the Claude Code plugin curated while deferring a native Codex one. **The same
constraint applies to us** — keep it in mind before assuming `.codex-plugin/plugin.json` can
curate a subset of `skills/` the way `.claude-plugin/plugin.json` can.

## Explicitly out of scope (`.out-of-scope/`)

When someone asks for something this repo deliberately won't do, write it down instead of
re-explaining it every time it comes up: what was asked, why it's out of scope, what the existing
escape hatch is, and a pointer to where it was asked (a Slack thread or a Rocketlane task, in our
case — mattpocock links GitHub issues). Example from his repo:
`.out-of-scope/question-limits.md`.

## Plugin manifests

`.claude-plugin/plugin.json`'s `skills` field should be an **explicit array of skill-directory
paths** — not a wildcard string. This is deliberate curation: it's how deprecated or in-progress
skills stay out of what actually gets installed, exactly as mattpocock's own ADR describes. Update
this array whenever a skill is promoted, and update `version` here alongside the skill's own
`version:` bump if the two are meant to move together (they don't have to — see "Versioning"
above).

`.codex-plugin/plugin.json` cannot do the same curation — its `skills` field only accepts a single
path string, and Codex drops symlinks on install. Until that changes upstream, treat the Codex
manifest as "ships everything under `skills/`" and rely on the category README's own promote/
absorb/deprecate status to communicate what's actually meant to be used.

## What we deliberately did not copy from mattpocock

- **Repo-wide semver / Changesets** — see "Versioning" above.
- **A CI release workflow** — his `release.yml` runs `changesets/action` on every push to `main`;
  we don't need that without repo-wide versioning. Revisit if that changes.
- **An installer CLI** (`skills.sh` / `npx skills add`) — not needed at our current scale. Revisit
  once there are enough skills that copy-pasting from GitHub gets painful.
