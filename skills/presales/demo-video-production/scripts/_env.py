"""Credential loading shared by every script in this skill.

Lookup order for each variable (first hit wins):
  1. The process environment (`export ELEVENLABS_API_KEY=...`).
  2. `~/.config/vtex-se-skills/.env` — the recommended per-user location, outside any repo.
  3. A `.env` in the current working directory or any of its parents.

Values are never printed or logged. The skill folder itself never holds a real `.env` — only
`.env.example` with the variable names.
"""
import os
import sys
from pathlib import Path

USER_ENV = Path.home() / ".config" / "vtex-se-skills" / ".env"


def _candidate_files() -> list[Path]:
    files = [USER_ENV]
    cwd = Path.cwd().resolve()
    files += [d / ".env" for d in (cwd, *cwd.parents)]
    return files


def _read_dotenv(path: Path, name: str) -> str | None:
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return None
    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):]
        if line.startswith(f"{name}="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def find_env_var(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    for path in _candidate_files():
        if path.is_file():
            value = _read_dotenv(path, name)
            if value:
                return value
    return None


def load_env_var(name: str) -> str:
    value = find_env_var(name)
    if value:
        return value
    sys.exit(
        f"{name} is not set. Put it in {USER_ENV} (see .env.example in this skill's folder) "
        "or export it in your shell. Ask the skill maintainers for the value — never commit it."
    )
