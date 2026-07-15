# mcp-dev-skills

A portable, model-agnostic **MCP (Model Context Protocol) server** exposing a suite
of sandboxed developer skills. It is fully self-contained: push it to GitHub, clone
it into any workspace, and it exposes tools scoped to that project via a
`.skills.json` policy file.

- **Transport:** `stdio` (works with Claude Desktop, Cursor, Windsurf, and custom clients)
- **Sandbox-first:** every path operation is validated against the workspace root
  (`Path.cwd()`); no absolute project paths are ever hardcoded.
- **Dynamic tool discovery:** which tools are exposed is decided at runtime by the
  target workspace's `.skills.json`.

## Skills (v1.0.0)

| Skill | Purpose | Args |
| --- | --- | --- |
| `analyze_project_structure` | Lightweight recursive tree + structural hints (languages, config files), respecting `.gitignore`. | `depth` (int, default 3) |
| `safe_read_file` | Read a file's contents with path-sandboxing checks. | `file_path` (string, required) |

## Requirements

- Python **3.10+**

## Install / build

```bash
# clone, then from the repo root:
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash);  use .venv/bin/activate on macOS/Linux
pip install -e .
```

This installs the `mcp-dev-skills` console script (equivalent to
`python -m mcp_dev_skills`).

## Run

The server speaks MCP over stdio, so it is normally launched by an MCP client, not
by hand. To smoke-test that it starts:

```bash
python -m mcp_dev_skills   # waits for a client on stdin/stdout; Ctrl-C to exit
```

## Configure in Claude Desktop

Edit your `claude_desktop_config.json` and add an entry using the **absolute path**
to the Python interpreter in your virtualenv (or a global Python that has the package
installed). The server sandboxes to its working directory (`cwd`), so point `cwd` at
the project you want the skills to operate on.

```json
{
  "mcpServers": {
    "dev-skills": {
      "command": "C:\\path\\to\\project\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_dev_skills"],
      "cwd": "C:\\path\\to\\target\\workspace"
    }
  }
}
```

On macOS/Linux use `.venv/bin/python` and POSIX paths.

## The `.skills.json` policy file

Place a `.skills.json` in the **target workspace** (the `cwd` above) to control which
tools are exposed there. Copy [`.skills.json.example`](.skills.json.example) as a start:

```json
{
  "enabled_skills": [
    "analyze_project_structure",
    "safe_read_file"
  ],
  "disabled_skills": [
    "execute_db_query"
  ]
}
```

Rules:

- **No `.skills.json`** → only the default read-only safe toolset is exposed
  (`analyze_project_structure`).
- **`.skills.json` present** → only tools listed in `enabled_skills` are exposed, and
  anything in `disabled_skills` is removed even if also enabled.
- Calling a disabled tool returns:
  `Tool [tool_name] is disabled by the current project's configuration (.skills.json)`
- The file is re-read on every request, so policy edits take effect without a restart.

## Security model

All file paths passed to tools are resolved relative to the workspace root and
verified to stay inside it. Absolute paths (`/etc/passwd`) and traversal
(`../../etc/passwd`) are rejected with a sandbox-violation error before any I/O.

## Repository layout

```
├── .gitignore
├── README.md
├── pyproject.toml
├── requirements.txt
├── .skills.json.example
└── src/mcp_dev_skills/
    ├── __main__.py            # entry point: stdio transport & lifecycle
    ├── server.py              # server instance, tool registration & routing
    ├── config.py              # workspace discovery & .skills.json parser
    ├── security.py            # path resolution & sandbox validation
    └── tools/
        ├── project_analyzer.py
        └── file_operations.py
```
