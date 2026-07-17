# ShayaBrusilovskySkills — Project Status & Skills Inventory

**Last updated:** 2025-07-17  
**Model:** Claude Haiku 4.5  
**Status:** Core architecture complete, core skills implemented

---

## 📊 Project Overview

MCP (Model Context Protocol) server exposing a hierarchical library of **developer skills** for managing multi-app projects via **Trello** and **git branches**, with flexible configuration per project.

**Total Skills:** 18 (across 4 groups)

---

## 🎯 What's Done

### ✅ Core Architecture
- [x] Hierarchical skill discovery via dot-notation paths (e.g., `development.trello`)
- [x] Dynamic loader with wildcard support (`development.*`)
- [x] Configuration via `.skills.json` with `enabled_paths` selection
- [x] Sandbox security (path validation, workspace isolation)
- [x] MCP server with stdio transport
- [x] Trello REST API integration with UTF-8 encoding

### ✅ Skill Groups Implemented

#### 1. **development.common** (4 skills)
- Project analysis and file operations
- Interactive skill configuration setup
- Universal three-stage development methodology (Design → Deployment → Testing)

#### 2. **development.trello** (12 skills)
- Trello board configuration with scopes
- Smart workflow skills (set_plan, ask_questions, change_status)
- Atomic Trello operations (get_card, add_comment, monitor_board, etc.)
- Multi-app scope management (switch_scope with known_scopes tracking)
- Language auto-detection (Russian/English/mixed)
- Tech-level filtering (0-3 scale for question complexity)

#### 3. **development.branching** (1 skill)
- Simple branching workflow strategy
- Assign card to branch, update status, list active branches
- Modular design for future strategies (with_pr, feature_branch, etc.)

#### 4. **development.local_dev** (1 skill)
- Local development rules (instructions, no executable code yet)
- Strategy-based: currently `local_dev_default`
- Future: multiple strategies (strict, minimal, etc.)

---

## 📁 Project Structure

```
ShayaBrusilovskySkills/
├── src/mcp_dev_skills/
│   ├── server.py                    # MCP server
│   ├── loader.py                    # Dynamic skill discovery
│   ├── config.py                    # .skills.json loading
│   ├── security.py                  # Path sandboxing
│   └── skills/development/
│       ├── common/
│       │   ├── project_analyzer.py
│       │   ├── file_operations.py
│       │   ├── setup_skills.py
│       │   └── development_methodology.py
│       ├── trello/
│       │   ├── configure.py
│       │   ├── set_plan.py          # Smart: auto-backup original task
│       │   ├── ask_questions.py     # Smart: Q&A with tech-level filter
│       │   ├── change_status.py     # Smart: validate workflow rules
│       │   ├── monitor_board.py     # Poll every 3s, silent until work
│       │   ├── switch_scope.py      # Multi-app switching
│       │   ├── get_card.py
│       │   ├── add_comment.py
│       │   ├── add_checklist_item.py
│       │   ├── create_checklist.py
│       │   ├── move_card.py
│       │   ├── update_card_description.py
│       │   └── config_utils.py      # Shared Trello utilities
│       ├── branching/
│       │   └── branching_simple.py  # Strategy: simple workflow
│       └── local_dev/
│           └── local_dev_default.py # Strategy: default local rules
├── .skills.json                     # Configuration
├── SKILLS_GUIDE.md                  # User documentation
├── WORKFLOW.md                       # Trello workflow protocol
└── PROJECT_STATUS.md                # This file

Total: 18 skill files (+ utilities)
```

---

## 📋 Detailed Skill Inventory

### GROUP: development.common

#### **1. project_analyzer**
- **Description:** Recursively scan workspace and return lightweight tree structure
- **Use:** Understand project layout
- **Input:** None (workspace auto-detected)
- **Output:** JSON tree or formatted text

#### **2. file_operations**
- **Description:** Safely read workspace files (path-sandboxed)
- **Use:** Read code, config, docs with security boundaries
- **Input:** `file_path` (relative to workspace)
- **Output:** File contents or error

#### **3. setup_skills**
- **Description:** List available skills and generate `.skills.json` config
- **Use:** Interactive onboarding, discover what's available
- **Input:** `action` (list_tree or generate_config)
- **Output:** Skill tree or config file

#### **4. development_methodology**
- **Description:** Universal three-stage development system (Design → Deployment → Testing)
- **Use:** Track progress on any feature, module, skill, or system
- **Application:** Project-agnostic, scope-agnostic, language-agnostic
- **Stages:**
  - **Проектирование (Design):** Understand requirements, design solution, make decisions
  - **Развертывание (Deployment):** Implement design, deploy to environment
  - **Тестирование (Testing):** Verify everything works, catch edge cases
- **Output:** Formatted methodology guide with examples

**Development Stages:**
- [x] Design
- [ ] Deployment (waiting for real project)
- [ ] Testing

---

### GROUP: development.trello

#### **Trello Configuration**

**4. configure_trello**
- **Type:** Configuration/Setup
- **Description:** Set up Trello board: validate credentials, create missing columns
- **Automatically:**
  - Fetches board info
  - Creates columns: Inbox, Planning, Approved, In Progress, Review, Done
  - Saves config to `.claude/trello.json`
- **Input:**
  - `board_url`: Full Trello board URL
  - `api_key`: Trello API key
  - `token`: Trello token
  - `scope`: App name (e.g., "rental", "crm") — optional, default "default"
  - `tech_level`: 0-3 for tech-question filtering — optional, default 1
- **Output:** Confirmation + column status
- **Config file stored:** `.claude/trello.json`
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

**5. switch_scope**
- **Type:** Configuration/Management
- **Description:** Switch between configured Trello boards or mark scopes as known
- **Actions:**
  - List all known/configured scopes
  - Switch active scope
  - Mark future scopes as known (planned)
- **Input:**
  - `scope`: Scope to switch to — optional
  - `mark_known`: Comma-separated scopes to register — optional
- **Output:** List of scopes or confirmation
- **Status symbols:**
  - `✓` = Configured (has Trello board)
  - `○` = Known/planned (registered but not configured yet)
  - `← current` = Currently active

---

#### **Smart Workflow Skills** (embed workflow rules in code)

**6. set_plan**
- **Type:** Smart workflow
- **Rule:** Save original task before overwriting
- **Description:** Write plan to card description, auto-save original task to comment
- **Automatically:**
  - Detects task language (Russian/English/mixed)
  - Saves original description to comment (one-time)
  - Writes plan to description
  - Stores detected language in config
- **Input:**
  - `card_id`: Trello card ID
  - `plan`: Plan text (any language)
- **Output:** Confirmation with language detected
- **Example:**
  ```python
  set_plan(
    card_id="5f8d9a2b1c3e4f5a",
    plan="Шаг 1: настроить OAuth\nШаг 2: добавить тесты"
  )
  # → Language auto-detected: Russian
  # → Original saved to comment
  # → Plan written to description
  ```

**7. ask_questions**
- **Type:** Smart workflow
- **Rule:** Filter tech questions by user level
- **Description:** Create Questions/Answers checklists, filtered by user's tech level
- **Automatically:**
  - Loads user's tech_level from config
  - Filters questions (tech_level=0 skips technical questions)
  - Creates Questions checklist with filtered questions
  - Creates empty Answers checklist (user fills in)
  - Moves card to Planning
- **Input:**
  - `card_id`: Trello card ID
  - `questions`: List of questions (e.g., ["1) Goal?", "2) Language?"])
- **Output:** Confirmation with skip count if applicable
- **Tech detection:** Keywords (язык, программирование, code, database, api, etc.)
- **Example:**
  ```python
  ask_questions(
    card_id="...",
    questions=[
      "1) What is the goal?",
      "2) What programming language?",  # ← skipped for tech_level=0
      "3) When needed?"
    ]
  )
  # For tech_level=0:
  # → Creates: 2 questions (skipped 1 technical)
  ```

**8. change_status**
- **Type:** Smart workflow
- **Rule:** Validate workflow state transitions
- **Description:** Move card with validation of allowed transitions
- **Workflow rules:**
  - Claude can: `Inbox→Planning`, `Approved→In Progress`, `In Progress→Review`
  - User only: `Planning→Approved`, `Review→Done`
- **Prevents:** Accidental invalid moves (e.g., Claude can't move to Approved)
- **Input:**
  - `card_id`: Trello card ID
  - `new_status`: Target column (Inbox, Planning, Approved, In Progress, Review, Done)
- **Output:** Confirmation or error (with allowed transitions)
- **Example:**
  ```python
  change_status(card_id="...", new_status="In Progress")
  # ✓ OK: Approved → In Progress
  
  change_status(card_id="...", new_status="Approved")
  # ✗ Error: Cannot move to Approved (user decision)
  ```

---

#### **Trello Operations** (atomic, low-level)

**9. monitor_board**
- **Type:** Atomic operation
- **Description:** Poll Trello board silently, alert when work appears
- **Behavior:**
  - Polls every 3 seconds
  - SILENT when no work
  - Alerts when work found in [Approved] or [Inbox]
- **Input:** None
- **Output:** Nothing (silent) or "WORK found: [list]"
- **Use:** Run in background loop

**10. get_card**
- **Type:** Atomic operation
- **Description:** Read full card details
- **Returns:** name, description, labels, all checklists with item status, comments
- **Input:** `card_id`
- **Output:** JSON card object

**11. add_comment**
- **Type:** Atomic operation
- **Description:** Add comment to card
- **Automatically:** Prefixes Claude comments with `🤖 `
- **Input:** `card_id`, `text`
- **Output:** Confirmation

**12. add_checklist_item**
- **Type:** Atomic operation
- **Description:** Add single item to checklist
- **Input:** `checklist_id`, `text`
- **Output:** Confirmation

**13. create_checklist**
- **Type:** Atomic operation
- **Description:** Create empty checklist on card
- **Input:** `card_id`, `name` (e.g., "Questions", "Review points")
- **Output:** Checklist ID + confirmation

**14. move_card**
- **Type:** Atomic operation
- **Deprecated:** Use `change_status` instead (has validation)
- **Description:** Move card to column by name
- **Input:** `card_id`, `list_name`
- **Output:** Confirmation

**15. update_card_description**
- **Type:** Atomic operation
- **Deprecated:** Use `set_plan` instead (auto-saves original)
- **Description:** Update card description
- **Input:** `card_id`, `plan`
- **Output:** Confirmation

---

### GROUP: development.branching

#### **1. branching_simple**
- **Type:** Strategy (one complete workflow)
- **Description:** Simple git branching: create branch, update status, list active branches
- **All functions in one file** (git utils inline, Trello utils imported)
- **Actions:**
  - `action="assign"`: Create git branch for Trello card
    - Input: `card_id`, `branch_name`, `agent_id`
    - Creates local branch from main
    - Adds Trello comment with branch info
    - Moves card to "In Progress"
  - `action="update_status"`: Sync git status to Trello
    - Input: `card_id`, `branch_name` (optional, auto-detect from Trello)
    - Gets commit count from git
    - Updates Trello comment with progress
  - `action="list"`: Show all active branches
    - Input: `filter` (optional, e.g., "crm-")
    - Returns: list of branches with commit count
- **Example:**
  ```python
  branching_simple(
    action="assign",
    card_id="...",
    branch_name="crm-auth-oauth",
    agent_id="claude"
  )
  # → git branch created
  # → Trello comment added
  # → Card → In Progress
  
  branching_simple(action="list", filter="crm-")
  # → crm-auth-oauth (5 commits)
  # → crm-cache-redis (3 commits)
  ```

---

### GROUP: development.local_dev

#### **1. local_dev_default**
- **Type:** Strategy (ruleset, instructions only)
- **Description:** Default rules for local (non-production) development
- **No executable code** — returns formatted instructions
- **Rules covered:**
  1. **Local Environment Setup**
     - Local DB ≠ production (SQLite local, PostgreSQL prod)
     - Separate `.env.local`, never commit real credentials
  2. **Mock/Test Data**
     - Test user passwords = usernames (alice → alice)
     - Obviously fake data (clear names, example emails)
  3. **Development Config**
     - Debug mode + verbose logging (off in prod)
     - Fast feedback: mock external services
  4. **Workflow Helpers**
     - Visual indicator that you're on local (banner, env label, etc.)
- **Future strategies:** `local_dev_strict`, `local_dev_minimal`, etc.
  User picks one via `.skills.json` `enabled_paths`

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

### Enable Only Trello
```json
{
  "enabled_paths": [
    "development.common",
    "development.trello"
  ]
}
```

### Disable branching, keep local_dev
```json
{
  "enabled_paths": [
    "development.common",
    "development.trello",
    "development.local_dev"
  ]
}
```

---

## 📚 Related Documentation

- **SKILLS_GUIDE.md** — Full user guide with examples
- **WORKFLOW.md** — Trello workflow protocol, conventions, API reference
- **.claude/trello.json** — Runtime config (auto-created by configure_trello)

---

## 🚀 Next Steps

- [ ] Expand `local_dev_default` with concrete test data examples
- [ ] Create `branching_with_pr` strategy (with PR creation)
- [ ] Create alternative local strategies (`local_dev_strict`, etc.)
- [ ] Add CI/CD group for deployment skills
- [ ] Add CLI scaffolding group for quick project setup

