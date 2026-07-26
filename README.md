# mcp-dev-skills

Portable, model-agnostic **MCP (Model Context Protocol) server** with a hierarchical library of **smart developer skills** — tools and rules you attach to a project so agents follow real engineering discipline, not ad-hoc improvisation.

**North star:** encode programmer experience as selectable skills (analysis, safe file ops, methodology, local-dev rules, branching helpers) and enable only what each project needs via `.skills.json`.

| Status | Detail |
| --- | --- |
| Maturity | Early (core solid; skills uneven) — Phase A: docs truth + core tests + Trello frozen |
| Transport | `stdio` (Claude Desktop, Cursor, Windsurf, custom clients) |
| Security | Path sandbox relative to workspace root; no hardcoded project paths |
| Loading | Dot-notation paths + wildcards; config re-read every request |

## Architecture

```
skills/
├── development/
│   ├── common/                 # Core tools (default-safe)
│   │   ├── project_analyzer.py
│   │   ├── file_operations.py
│   │   └── setup_skills.py
│   ├── development_rules/      # Process / methodology rulesets
│   ├── local_dev/              # Local (non-prod) environment rules
│   ├── branching/              # Parallel branch helpers
│   ├── server_development/     # Autonomous server-dev rules
│   └── trello/                 # LEGACY/FROZEN optional board pack
└── …
```

Each skill module exports:

- `SKILL` — `name`, `group`, `description`, `input_schema`
- `execute(workspace_root, **kwargs)` — implementation

### Skill kinds

| Kind | Examples | Role |
| --- | --- | --- |
| **Tools** | `project_analyzer`, `file_operations`, `branching_simple` | Executable work in the workspace |
| **Rulesets** | `methodology_three_stage`, `local_dev_default`, `server_development_autonomous` | Instructions the agent should load and follow |
| **Legacy pack** | `trello`, `workflow_state` | Optional; code kept, **not enabled by default** |

## Skills (current tree)

### development.common (default when no config)

| Skill | Purpose |
| --- | --- |
| `project_analyzer` | Multi-level workspace analysis (tree / overview / part / paths) |
| `file_operations` | Sandboxed read / write / delete with access-control map |
| `setup_skills` | List skill tree; generate `.skills.json` |

### development.development_rules

| Skill | Purpose |
| --- | --- |
| `methodology_three_stage` | Design → implement → test methodology + step-by-step protocol |

### development.local_dev

| Skill | Purpose |
| --- | --- |
| `local_dev_default` | Rules for safe local/non-production work |

### development.branching

| Skill | Purpose |
| --- | --- |
| `branching_simple` | Create / list / finish parallel branches |

### development.server_development

| Skill | Purpose |
| --- | --- |
| `server_development_autonomous` | Rules when no human is in the loop |

### development.trello — LEGACY / FROZEN

Board-polling pack (single `trello` tool + `workflow_state`). **Not in default or recommended config.**  
Code remains under `skills/development/trello/`. To re-enable:

```json
"enabled_paths": [ "…", "development.trello" ]
```

Details: [SKILLS_GUIDE.md](SKILLS_GUIDE.md) (legacy guide), [WORKFLOW.md](src/mcp_dev_skills/skills/development/trello/WORKFLOW.md).

## Quick Start

### 1. Install

```bash
git clone <repo>
cd mcp-dev-skills
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -e ".[dev]"
# or:
pip install -e .
pip install pytest
```

### 2. Configure skills

```bash
python -m mcp_dev_skills setup
```

Or copy the example:

```bash
copy .skills.json.example .skills.json   # Windows
# cp .skills.json.example .skills.json  # Unix
```

Recommended baseline (smart rules, no board):

```json
{
  "enabled_paths": [
    "development.common",
    "development.branching",
    "development.local_dev",
    "development.development_rules",
    "development.server_development"
  ],
  "disabled_skills": []
}
```

### 3. Wire into Claude Desktop (or similar)

```json
{
  "mcpServers": {
    "dev-skills": {
      "command": "C:\\path\\to\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_dev_skills"],
      "cwd": "C:\\path\\to\\your\\project"
    }
  }
}
```

Use `.venv/bin/python` on macOS/Linux. `cwd` must be the **target project** workspace (sandbox root).

## `.skills.json`

| Path | Loads |
| --- | --- |
| `"development.common"` | Core tools only |
| `"development.development_rules"` | Methodology rulesets |
| `"development.*"` | Entire development tree (**includes frozen Trello**) |
| `"*"` | Everything |
| omit file | Default: `development.common` only |

- Empty `enabled_paths` → no skills exposed  
- `disabled_skills` → exclude specific skill names  
- Config is re-read on every MCP request (no restart needed)  
- Extra keys (e.g. `notes`) are ignored by the loader  

## Security

- Paths resolve relative to the workspace root and must stay inside it  
- Absolute paths and `..` escapes are rejected (`PathEscapeError`)  
- Prefer least privilege: enable only the paths a project needs  

## Repository layout

```
.
├── .skills.json / .skills.json.example
├── README.md
├── PROJECT_STATUS.md / PROJECT_STATUS_RU.md
├── pyproject.toml
├── tests/
│   ├── test_core_config.py
│   ├── test_core_loader.py
│   ├── test_core_security.py
│   └── test_trello_skills.py          # legacy pack (still run when present)
└── src/mcp_dev_skills/
    ├── __main__.py
    ├── server.py
    ├── config.py
    ├── loader.py
    ├── security.py
    ├── setup.py
    ├── monitor.py                     # Trello wait-loop (legacy)
    └── skills/development/…
```

## Development

### Tests

```bash
pytest
```

### Adding a skill

1. Create `skills/<group>/.../my_skill.py` with `SKILL` + `execute`.
2. Enable the group path in the target project's `.skills.json`.
3. Prefer tests under `tests/` for any tool that touches FS, git, or network.

```python
SKILL = {
    "name": "my_new_skill",
    "group": "development.example",
    "description": "What this skill does",
    "input_schema": {
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "..."}
        },
    },
}

def execute(workspace_root, **kwargs):
    return "result"
```

### Historical notes

- `tech.md` — original product brief (partially outdated; Python was chosen over TypeScript).  
- Trello pack — first polished skill pack (remote browser tasking → one-machine agent). Frozen so it does not drive the product narrative.

## License

MIT
