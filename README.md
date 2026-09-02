# vtex-se-skills

Central repository for skills (Claude Code / agent skills) built by the VTEX Solution Engineering
team.

**Status: under construction.** This repo is aggregating skills that exist scattered across the
team today (individual repos, personal forks, local `.claude` directories) into one place, as
part of the "SE Co-pilot — 90 Day Plan" (Rocketlane #1442908).

**Not curated yet.** Skills landing here have only been collected, not reviewed, tested, or
standardized against each other. Don't assume quality, active maintenance, or that a skill works
out of the box as-is. Deciding promote / absorb / deprecate for each one, item by item, is still
in progress.

## Structure

Adapted from [gstack](https://github.com/garrytan/gstack),
[superpowers](https://github.com/obra/superpowers), and
[mattpocock/skills](https://github.com/mattpocock/skills) — mostly following mattpocock's
layout, plus per-skill versioning from gstack:

- `AGENTS.md` / `CLAUDE.md` — same content, so Claude Code and other agent runtimes pick up the
  same rules. `GEMINI.md` imports `AGENTS.md` for Gemini.
- `CONTEXT.md` — VTEX-specific vocabulary (SE, Rocketlane, Atlas, FastStore, and so on).
- `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `gemini-extension.json` — plugin
  manifests so this repo can be installed directly in each runtime.
- `skills/<category>/<skill-name>/SKILL.md` — one folder per skill, grouped by category. Each
  skill's own `SKILL.md` carries its own `version:` field in the frontmatter (skills evolve
  independently via PR, not on a shared repo-wide version). Categories:
  - `skills/presales/` — solution design, demo building, and other customer-facing prep. RFP
    response is out of scope here, handled separately together with Atlas.
  - `skills/governance/` — reporting, health checks, and internal process tooling.
  - `skills/in-progress/` — being built or actively reworked.
  - `skills/deprecated/` — replaced or absorbed, kept for history.

No skill has been migrated in yet. Tracked in Rocketlane task #43751748.

## Contributing

Anyone on the SE team can open a PR adding or adjusting a skill. Djan Magno and Noé Eustaquio
review and merge.

## Contact

Djan Magno, Noé Eustaquio — VTEX Solution Engineering.
