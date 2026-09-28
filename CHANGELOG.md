# Changelog

This repo doesn't version as a whole (see `CONTRIBUTING.md` — versioning is per skill, not per
repo), so entries here are grouped by date and cite the commit, not a release tag.

## 2026-09-28

### Added

- **`demo-video-production`** (Djan Magno, Noé Eustaquio): `v1.0.0`, under `skills/presales/`. It
  is the first **user-invoked** skill (`disable-model-invocation: true`, because it spends
  ElevenLabs/RunPod credits).
  - Packages the team's demo-video pipeline in two modes: re-editing an existing recording, and
    building a video from scratch.
  - Ships its own new-user `README.md` (setup, keys, costs, troubleshooting) alongside
    `docs/presales/demo-video-production.md`.
  - Scripts were adapted to load keys from the environment or `~/.config/vtex-se-skills/.env`, and
    new ones were added: `speech_to_speech.py`, `build_slides.py`, `assemble.py`,
    `capture_chrome_window.sh`, `check_setup.sh`.

  (`5ea5224`)
- **Root `.gitignore`**: blocks `.env` files and Python caches, so nobody can commit a key by
  accident. (`5ea5224`)

### Changed

- **`skills/presales/README.md`** now has separate **User-invoked** / **Model-invoked** sections,
  per `CONTRIBUTING.md`, since the category contains both kinds. (`5ea5224`)

## 2026-09-02

### Added

- **`README.md`**: status, scope (aggregating scattered team skills, not curated yet), and the
  planned structure adapted from `gstack`, `superpowers`, and `mattpocock/skills`. (`a91ed98`)
- **Repo scaffold**: `AGENTS.md`/`CLAUDE.md` (same content), `CONTEXT.md` starter glossary,
  `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` manifests, and the four category folders
  (`presales/`, `governance/`, `in-progress/`, `deprecated/`) each with an index `README.md`.
  (`cb4f671`)
- **`CONTRIBUTING.md`**: the full skill format standard (structure, per-skill `version:`,
  user-invoked vs. model-invoked, `docs/` companion pages, ADRs, `.out-of-scope/`, explicit plugin
  manifest curation), written after a complete read of `mattpocock/skills`'s conventions. (`15e742a`)
- **First 3 skills migrated**, each with a `docs/presales/<skill>.md` companion and a `version:`
  field added to `SKILL.md` frontmatter (none of the sources had one):
  - `vtex-brand-guidelines` (Diego Cione) — `v0.1.0`
  - `stakeholder-scout` (Diego Cione, from `se-scout-service`) — `v1.0.0`
  - `solution-design` (João Guilherme Porto) — `v0.2.0`
  (`15e742a`)
- **`CONTRIBUTING.md`** section on hard dependencies on externally-maintained skills, using
  `vams-to-miro` as the precedent case. (`7d2b1a5`)

### Changed

- **Runtime support**: replaced Gemini CLI support (`GEMINI.md`, `gemini-extension.json`) with
  documentation of Antigravity (Gemini CLI's successor, discovers `AGENTS.md` automatically, skill
  discovery deferred) and Grok Build (needs no manifest, reads Claude Code artifacts directly).
  Reason: Gemini CLI was retired 2026-06-18. (`16bccf0`)

### Removed

- **`vams-to-miro`**, vendored copy. It's Miguel Carrera's skill, actively maintained and
  distributed via `#ai-committee`, and its output feeds Atlas's knowledge-base ingestion pipeline.
  A `diff -rq` against Miguel's original 2026-07-28 file confirmed the vendored copy was byte-
  identical (only the added `version:` field differed) — no drift existed at the time, but keeping
  a copy here would create exactly the second-source-of-truth risk `CONTRIBUTING.md` warns against,
  with higher stakes than usual because of the Atlas dependency. `solution-design`'s docs now list
  it as an external prerequisite to install separately. (`7d2b1a5`)
- **`GEMINI.md`**, **`gemini-extension.json`** — see "Changed" above. (`16bccf0`)
