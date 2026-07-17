"""Skill: local_dev_default — default rules for local (non-production) development.

Returns a ruleset (instructions) the agent must follow when developing on
local data. This is the DEFAULT strategy. Other strategies can live alongside
in this folder; the user enables exactly one via .skills.json.

For now this is instructions only (no executable setup) — the agent reads the
rules and applies them when scaffolding local environments and test data.
"""

from __future__ import annotations

from pathlib import Path

SKILL = {
    "name": "local_dev_default",
    "group": "development.local_dev",
    "description": (
        "Default rules for comfortable local development on non-production data. "
        "Returns the ruleset to follow: local DB choice, test data, dev config, "
        "workflow helpers. Instructions only (agent applies them)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


RULES = """\
# Local Development Rules (default strategy)

Apply these rules when setting up and working in a LOCAL (non-production)
environment. Never apply them to production.

## 1. Local Environment Setup
- Local DB is NEVER the same engine/instance as production.
  Use a simple local engine with test data (e.g. SQLite locally, PostgreSQL
  in production). Local DB is disposable and safe to reset.
- Keep local config separate from production config (e.g. `.env.local`),
  and never commit real production credentials.

## 2. Mock / Test Data
- Seed the local DB with a small, readable set of test data.
- Test user passwords equal their username/name, so they are trivial to
  remember and never confused (e.g. user `alice` -> password `alice`).
- Test data should be obviously fake (clear names, example emails) so it is
  never mistaken for real user data.

## 3. Development Config
- Enable debug mode and verbose logging locally (off in production).
- Prefer fast feedback: no external production services; stub or mock them.

## 4. Workflow Helpers
- Make it obvious at a glance that you are on local (e.g. banner, prompt, or
  env label) so local and production are never confused.

---
This is the DEFAULT ruleset. To use a different strategy, enable another
module from `development/local_dev/` in `.skills.json` instead of this one.
"""


def execute(workspace_root: Path, **kwargs) -> str:
    """Return the local development ruleset for the agent to follow."""
    return RULES
