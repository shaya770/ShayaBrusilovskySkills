# ShayaBrusilovskySkills — Project Status & Skills Inventory

**Last updated:** 2026-07-17
**Status:** Core architecture complete; Trello consolidated into a single skill

---

## 📊 Project Overview

MCP (Model Context Protocol) server exposing a hierarchical library of **developer skills** for managing multi-app projects via **Trello** and **git branches**, with flexible configuration per project.

**Total Skills:** 8 (across 4 groups)

---

## 🎯 What's Done

### ✅ Core Architecture
- [x] Hierarchical skill discovery via dot-notation paths (e.g., `development.trello`)
- [x] Dynamic loader with wildcard support (`development.*`)
- [x] Configuration via `.skills.json` with `enabled_paths` selection
- [x] Sandbox security (path validation, workspace isolation)
- [x] MCP server with stdio transport
- [x] Shared Trello HTTP client (`trello_api.py`) with real error reporting (401/404/429 distinguished)
- [x] Scope-aware config everywhere (`config_utils.py`) — no more flat-format leftovers

### ✅ 2026-07-17 Consolidation
- [x] 12 separate Trello skills merged into **one `trello` skill** with an `action` parameter
- [x] `monitor_board` (infinite polling loop — blocked the MCP server) replaced by one-shot `check_board` + standalone background monitor (`src/mcp_dev_skills/monitor.py`: silent until work, prints and exits → wakes Claude, zero tokens while idle)
- [x] Deprecated skills removed (`move_card`, `update_card_description`) — workflow validation can no longer be bypassed
- [x] New `workflow_state` skill — full context snapshot in one call
- [x] `.claude/trello.json` added to `.gitignore` (credentials never committed)
- [x] **BoardBackend abstraction** (`backend.py`) — all workflow code talks to a neutral board interface (lists/cards/comments/checklists); Trello is just the first implementation. Migration to the own web interface = implement `WebBackend`, register it in `_BACKENDS`, set `"backend": "web"` in config. Nothing else changes.

---

## 📁 Project Structure

```
ShayaBrusilovskySkills/
├── src/mcp_dev_skills/
│   ├── server.py                    # MCP server
│   ├── monitor.py                   # Background wait-for-work monitor (not an MCP tool)
│   ├── loader.py                    # Dynamic skill discovery
│   ├── config.py                    # .skills.json loading
│   ├── security.py                  # Path sandboxing
│   └── skills/development/
│       ├── common/
│       │   ├── project_analyzer.py
│       │   ├── file_operations.py
│       │   ├── setup_skills.py
│       │   ├── development_methodology.py
│       │   └── workflow_state.py    # NEW: context snapshot
│       ├── trello/
│       │   ├── trello.py            # THE board skill (10 actions, backend-agnostic)
│       │   ├── backend.py           # BoardBackend interface + TrelloBackend + get_backend()
│       │   ├── errors.py            # Neutral BoardAPIError (skills catch only this)
│       │   ├── trello_api.py        # Trello HTTP client (used only by TrelloBackend)
│       │   ├── config_utils.py      # Scope-aware config helpers
│       │   └── WORKFLOW.md
│       ├── branching/
│       │   └── branching_simple.py  # Strategy: simple workflow (uses trello_api)
│       └── local_dev/
│           └── local_dev_default.py # Strategy: default local rules
├── .skills.json                     # Configuration
├── SKILLS_GUIDE.md                  # User documentation
└── PROJECT_STATUS.md                # This file
```

---

## 📋 Detailed Skill Inventory

### GROUP: development.common (5 skills)

#### **1. project_analyzer**
- Three-level workspace analysis: overview → part details → exact file paths (+ level 0 tree view)
- Detects language/framework, partitions project into logical parts

#### **2. file_operations**
- Safely read workspace files (path-sandboxed)

#### **3. setup_skills**
- List available skills and generate `.skills.json` config

#### **4. development_methodology**
- Universal three-stage system: Design → Deployment → Testing
- **Stages:** Design [x], Deployment [x], Testing [ ]

#### **5. workflow_state** *(new)*
- One-shot snapshot for session start: current Trello scope/board, cards in working columns (with ids), git branch, dirty files, recent commits
- Works even when Trello is not configured (shows git only)

---

### GROUP: development.trello (1 skill, 10 actions)

#### **trello** — all Trello operations dispatched by `action`

| Action | What it does |
|---|---|
| `configure` | Validate credentials, create missing columns, save scope config |
| `switch_scope` | List boards / switch active scope / mark planned scopes |
| `check_board` | **One-shot** check for work in Inbox/Approved (no polling — the loop belongs to the client) |
| `get_card` | Full card details: description, labels, checklists (with ids), comments |
| `set_plan` | Write plan to description; auto-backup original task to comment; detect language |
| `ask_questions` | Questions/Answers checklists, filtered by user's tech_level; moves card to Planning |
| `change_status` | Move card **with workflow validation** (see rules below) |
| `add_comment` | Add comment (auto-prefixed 🤖) |
| `create_checklist` | Create empty checklist on card |
| `add_checklist_item` | Add item to checklist |

**Workflow rules (enforced in code, no bypass path):**
- Claude may move: `Inbox→Planning`, `Approved→In Progress`, `In Progress→Review`
- Only the user moves: `Planning→Approved`, `Review→Done`

**Config** (`.claude/trello.json`, gitignored):
```json
{
  "api_key": "...",
  "token": "...",
  "current_scope": "rental",
  "known_scopes": ["crm", "rental"],
  "boards": {
    "rental": {
      "board_id": "...",
      "board_url": "...",
      "board_name": "...",
      "tech_level": 0,
      "language": "auto"
    }
  }
}
```

---

### GROUP: development.branching (1 skill)

#### **branching_simple**
- `action="assign"`: create git branch for card, comment on Trello, move to In Progress
- `action="update_status"`: sync commit count/list to Trello comment
- `action="list"`: show active branches with commit counts
- Uses the shared `trello_api` client

---

### GROUP: development.local_dev (1 skill)

#### **local_dev_default**
- Ruleset (instructions only): local env setup, mock/test data conventions, dev config, workflow helpers

---

## 🔧 How to Use

### Configuration (.skills.json)
```json
{
  "enabled_paths": [
    "development.common",
    "development.trello",
    "development.branching",
    "development.local_dev"
  ],
  "disabled_skills": []
}
```

### Monitoring pattern
- On demand: `trello(action='check_board')` — returns instantly.
- Continuous: `python -m mcp_dev_skills.monitor --workspace <path> --interval 30` launched as a **background process**. Silent while idle (Claude not woken → zero tokens); prints the card list and exits when work appears, which wakes Claude to start working. Never a loop inside an MCP tool call.

---

## 📚 Related Documentation

- **SKILLS_GUIDE.md** — Full user guide with examples
- **WORKFLOW.md** — Trello workflow protocol, conventions
- **.claude/trello.json** — Runtime config (auto-created by `trello action='configure'`, gitignored)

---

## 🚀 Next Steps

- [ ] Expand `local_dev_default` with concrete test data examples
- [ ] Create alternative local strategies (`local_dev_strict`, etc.)
- [ ] Add CI/CD group for deployment skills
- [ ] Add CLI scaffolding group for quick project setup
- [ ] project_analyzer: skip .venv/node_modules in framework detection (known issue)
