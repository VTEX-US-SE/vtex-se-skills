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

## Structure (planned)

Following the pattern of [gstack](https://github.com/garrytan/gstack),
[superpowers](https://github.com/obra/superpowers), and
[mattpocock/skills](https://github.com/mattpocock/skills):

- `AGENTS.md` / `CLAUDE.md` — same content, so Claude Code, Gemini, and other agent runtimes all
  pick up the same rules.
- `CONTEXT.md` — VTEX-specific vocabulary (SE, RFP, Rocketlane, Atlas, FastStore, and so on).
- `skills/<category>/<skill-name>/SKILL.md` — one folder per skill, grouped by category:
  - `skills/presales/`
  - `skills/governance/`
  - `skills/in-progress/`
  - `skills/deprecated/`

None of this is populated yet. Tracked in Rocketlane task #43751748.

## Contact

Djan Magno, Noé Eustaquio — VTEX Solution Engineering.
