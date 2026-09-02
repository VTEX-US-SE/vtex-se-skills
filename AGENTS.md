# vtex-se-skills — agent instructions

This repo collects skills used by the VTEX Solution Engineering team, packaged to run across
multiple agent runtimes (Claude Code, Codex, Cursor, Gemini).

## Status

Under construction, not curated yet. See `README.md` for the current scope and how to
contribute.

## How skills are organized

`skills/<category>/<skill-name>/SKILL.md` — one folder per skill. Each category folder has its
own `README.md` index. Categories:

- `skills/presales/`
- `skills/governance/`
- `skills/in-progress/`
- `skills/deprecated/`

## Versioning

Each skill's `SKILL.md` carries its own `version:` field in the frontmatter. Skills evolve
independently: any SE can open a PR adjusting any skill in this repo, reviewed and merged by
Djan Magno and Noé Eustaquio. There's no single repo-wide version.

## Vocabulary

See `CONTEXT.md` for VTEX-specific terms used across these skills.
