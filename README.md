# mcp-dev-skills

A portable, model-agnostic **MCP (Model Context Protocol) server** exposing a **hierarchical, modular library** of sandboxed developer skills. Push it to GitHub, clone it into any workspace, and it exposes only the skills you explicitly enable via `.skills.json`.

- **Transport:** `stdio` (works with Claude Desktop, Cursor, Windsurf, and custom clients)
- **Sandbox-first:** every path operation is validated against the workspace root (`Path.cwd()`); no absolute project paths are ever hardcoded.
- **Hierarchical skill groups:** organize 100s of skills into nested folders (e.g., `development/django/models/`, `deployment/docker/`)
- **Selective loading:** only skills under enabled paths are loaded into memory; no bloat.

## Architecture

Skills live in a hierarchy under `src/mcp_dev_skills/skills/`:

```
skills/
├── development/
│   ├── common/                    # Core skills always available
│   │   ├── project_analyzer.py
│   │   ├── safe_read_file.py
│   │   └── setup_skills.py
│   ├── trello/                    # Trello task workflow
│   │   ├── check_board.py
│   │   └── WORKFLOW.md
│   ├── django/                    # Django-specific (future)
│   └── frontend/                  # Frontend skills (future)
├── deployment/                    # Deployment & DevOps
│   ├── docker/
│   └── k8s/
└── ...
```

Each `.py` file is a skill module with:
- `SKILL`: dict with `name`, `group`, `description`, `input_schema`
- `execute(workspace_root, **kwargs)`: function that runs the skill

## Skills (v1.1.0)

### development.common

| Skill | Purpose |
| --- | --- |
| `analyze_project_structure` | Lightweight tree + structural hints (languages, config files), respects `.gitignore` |
| `safe_read_file` | Read a file's contents with path-sandboxing checks |
| `setup_skills` | List available skills & generate `.skills.json` configuration |

### development.trello

| Skill | Purpose |
| --- | --- |
| `trello` | **All Trello operations in one tool** (dispatched by `action`): configure, switch_scope, check_board, get_card, set_plan, ask_questions, change_status, add_comment, create_checklist, add_checklist_item. Workflow rules enforced in code. Config in `.claude/trello.json` (gitignored). |

## Quick Start

### 1. Install

```bash
git clone <repo>
cd mcp-dev-skills
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Run interactive setup (first time)

```bash
python -m mcp_dev_skills setup
```

This launches an interactive CLI to select which skill groups to enable. It generates `.skills.json` automatically.

Or create `.skills.json` manually:

```json
{
  "enabled_paths": [
    "development.common",
    "development.trello"
  ],
  "disabled_skills": []
}
```

### 3. Configure in Claude Desktop

Edit `claude_desktop_config.json`:

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

(Use `.venv/bin/python` on macOS/Linux.)

## The `.skills.json` Configuration File

### Dot-notation paths

`enabled_paths` uses dot-notation to select skill groups from the tree:

| Path | Loads |
| --- | --- |
| `"development.common"` | All skills under `skills/development/common/` |
| `"development.trello"` | All skills under `skills/development/trello/` |
| `"development.*"` | All skills under `skills/development/` (any subdir) |
| `"*"` | All skills everywhere |

### Example configurations

**Basic development:**
```json
{
  "enabled_paths": [
    "development.common"
  ]
}
```

**With Trello task management:**
```json
{
  "enabled_paths": [
    "development.common",
    "development.trello"
  ]
}
```

**Everything (full-stack):**
```json
{
  "enabled_paths": ["*"]
}
```

**With exclusions:**
```json
{
  "enabled_paths": ["development.*"],
  "disabled_skills": ["some_specific_skill"]
}
```

### Defaults

- **No `.skills.json`** → only `development.common` is enabled (safe, read-only set).
- **Empty `enabled_paths`** → no skills exposed.
- Config is re-read on every request, so edits take effect without restart.

## Trello Integration

### Setup

Enable `development.trello` in `.skills.json`:

```json
{
  "enabled_paths": [
    "development.common",
    "development.trello"
  ]
}
```

### Configuration

1. **Get Trello credentials:**
   - Go to https://trello.com/app-key
   - Copy **API Key**
   - Generate **Token** (authorize app)

2. **Configure via the `trello` skill:**
   - `trello(action="configure", board_url=..., api_key=..., token=..., scope=..., tech_level=...)`
   - Skill will:
     - ✓ Validate credentials
     - ✓ Check board exists
     - ✓ Create missing columns: Inbox, Planning, Approved, In Progress, Review, Done
     - ✓ Save config to `.claude/trello.json` (gitignored — never committed)

3. **Use board:**
   - `trello(action="check_board")` — one-shot check for actionable work

See [WORKFLOW.md](src/mcp_dev_skills/skills/development/trello/WORKFLOW.md) for full Trello task protocol.

## Security Model

- All file paths are resolved relative to the workspace root and verified to stay inside it.
- Absolute paths (`/etc/passwd`) and traversal (`../../secret`) are rejected.
- Tools run in the client's workspace sandbox; no network/system calls by default.

## Repository Layout

```
.
├── .gitignore
├── .skills.json              (generated by setup)
├── .skills.json.example
├── README.md
├── pyproject.toml
├── requirements.txt
│
└── src/mcp_dev_skills/
    ├── __main__.py           # entry point (server or setup CLI)
    ├── server.py             # MCP server, tool registration & routing
    ├── config.py             # .skills.json loader
    ├── loader.py             # dynamic skill discovery & loading
    ├── security.py           # path sandboxing utilities
    ├── setup.py              # interactive setup CLI
    │
    └── skills/               # hierarchical skill library
        └── development/
            ├── common/
            │   ├── project_analyzer.py
            │   ├── safe_read_file.py
            │   └── setup_skills.py
            └── trello/
                ├── check_board.py
                └── WORKFLOW.md
```

## Development

### Adding a new skill

1. Create a `.py` file in the appropriate `skills/` subdirectory.
2. Define `SKILL` dict and `execute()` function:

```python
# skills/development/example/my_skill.py

SKILL = {
    "name": "my_new_skill",
    "group": "development.example",
    "description": "What this skill does",
    "input_schema": {
        "type": "object",
        "properties": {
            "arg1": {
                "type": "string",
                "description": "..."
            }
        }
    }
}

def execute(workspace_root, **kwargs):
    arg1 = kwargs.get("arg1")
    # implement skill logic
    return result_string
```

3. The skill is automatically discovered on next server start.

### Adding a new skill group

Create the folder structure and add `__init__.py`:

```bash
mkdir -p src/mcp_dev_skills/skills/deployment/docker
touch src/mcp_dev_skills/skills/deployment/__init__.py
touch src/mcp_dev_skills/skills/deployment/docker/__init__.py
```

Then add `.py` files with skills inside `docker/`.

## License

MIT
