# ShayaBrusilovskySkills — Project Status & Skills Inventory

**Last updated:** July 18, 2026  
**Model:** Claude Haiku 4.5  
**Status:** Core architecture complete, skills implemented

---

## 📊 Project Overview

MCP (Model Context Protocol) server with hierarchical library of **developer skills** for multi-app management. Includes task management (Trello), git workflows, development rules and configuration.

**Structure:** 6 skill groups + dev_main (master configuration)  
**Total skills:** ~18 (tools + strategies)

---

## 🎯 What's Done

### ✅ Architecture
- [x] Hierarchical skill discovery (dot-notation: `development.trello`)
- [x] Dynamic loader with wildcards
- [x] Configuration via `.skills.json` with `enabled_paths`
- [x] Security (path sandbox, workspace isolation)
- [x] MCP server with stdio transport

### ✅ Implemented Skills
- [x] **development.common** — tools (project_analyzer, file_operations, setup_skills)
- [x] **development.trello** — task management (10 actions + workflow_state)
- [x] **development.branching** — parallel branch management
- [x] **development.local_dev** — local development rules
- [x] **development.development_rules** — development methodology strategies
- [x] **development.server_development** — autonomous development rules
- [x] **dev_main** — master project configuration and global settings

---

## 📁 Project Structure

```
ShayaBrusilovskySkills/
├── dev_main/                          # MASTER CONFIGURATION (in progress)
│   ├── dev_config.py                  # Orchestrator + configuration
│
├── src/mcp_dev_skills/
│   ├── server.py                      # MCP server
│   ├── loader.py                      # Dynamic skill loading
│   ├── config.py                      # Load .skills.json
│   ├── security.py                    # Path sandbox
│   │
│   └── skills/development/
│       │
│       ├── common/                    # TOOLS
│       │   ├── project_analyzer.py    # 3-level project analysis
│       │   ├── file_operations.py     # read/write/delete + access control
│       │   └── setup_skills.py        # skill configuration
│       │
│       ├── trello/                    # TASK MANAGEMENT
│       │   ├── trello.py              # 10 actions (configure, set_plan, etc)
│       │   ├── workflow_state.py      # context snapshot
│       │   ├── backend.py             # board abstraction
│       │   ├── trello_api.py          # HTTP client
│       │   ├── config_utils.py        # scope-aware config
│       │   └── errors.py              # error handling
│       │
│       ├── branching/                 # BRANCH MANAGEMENT
│       │   └── branching_simple.py    # create/list/finish parallel branches
│       │
│       ├── local_dev/                 # LOCAL DEV RULES
│       │   └── local_dev_default.py   # instructions (text only)
│       │
│       ├── development_rules/         # METHODOLOGY STRATEGIES
│       │   └── methodology_three_stage.py  # three stages + discussion protocol
│       │
│       └── server_development/        # AUTONOMOUS DEVELOPMENT
│           └── server_development_autonomous.py  # rule: no humans
│
├── .skills.json                       # Configuration
├── PROJECT_STATUS.md                  # This file (English)
└── PROJECT_STATUS_RU.md               # This file (Russian)

Total: ~18 skills + utilities
```

---

## 📋 Skills Inventory by Group

### **development.common** (3 tools)

#### 1. project_analyzer
- **Description:** Intelligent project analysis with 3 levels
- **Level 1:** Language, framework, project parts
- **Level 2:** Files/functions in selected part
- **Level 3:** Exact paths for editing
- **Status:**
  - [x] Design
  - [x] Deployment
  - [ ] Testing

#### 2. file_operations
- **Description:** Unified file operations interface
- **Actions:** read, write, delete, configure
- **Access levels:** read_write, read_only, forbidden
- **Config:** .project_structure.json
- **Status:**
  - [x] Design
  - [ ] Deployment
  - [ ] Testing

#### 3. setup_skills
- **Description:** List skills and generate configuration
- **Actions:** list_tree (show), generate_config (create)
- **Status:**
  - [x] Design
  - [x] Deployment
  - [ ] Testing

---

### **development.trello** (smart task management)

#### 1. trello (10 actions)
- **configure:** board setup + columns
- **switch_scope:** board switching
- **check_board:** one-shot work check
- **get_card:** full card details
- **set_plan:** write plan + auto-backup
- **ask_questions:** Q&A checklists with level filter
- **change_status:** move with workflow validation
- **add_comment:** add comment (🤖 prefix)
- **create_checklist:** create checklist
- **add_checklist_item:** add item to checklist
- **Built-in rules:** workflow validation, language detection, tech-level filter
- **Status:**
  - [x] Design
  - [x] Deployment
  - [x] Testing

#### 2. workflow_state
- **Description:** Context snapshot (Trello + Git) in one call
- **Use:** Restore context after session restart
- **Shows:** Current scope, working cards, git branch, commits
- **Status:**
  - [x] Design
  - [x] Deployment
  - [ ] Testing

---

### **development.branching** (branch management)

#### 1. branching_simple
- **Description:** Parallel branch management independent from current project
- **Actions:**
  - create: new branch (feature/bugfix/refactor)
  - list: show active branches
  - finish: test, push, merge to main
- **Feature:** Doesn't switch current branch when creating
- **Status:**
  - [x] Design
  - [x] Deployment
  - [ ] Testing

---

### **development.local_dev** (local rules)

#### 1. local_dev_default
- **Description:** Local development rules (instructions only)
- **Rules:**
  - Local DB ≠ production
  - Test user passwords = their names
  - Debug + verbose logging locally
  - Visual indicator you're on local
- **Future:** Other strategies (strict, minimal)
- **Status:**
  - [x] Design
  - [ ] Deployment
  - [ ] Testing

---

### **development.development_rules** (methodology strategies)

#### 1. methodology_three_stage
- **Description:** Development methodology for ShayaBrusilovskySkills
- **Three stages:**
  - Design (understand, architect, decide)
  - Deployment (implement, deploy)
  - Testing (verify, ensure quality)
- **Built-in:** Step-by-Step Discussion Protocol (one point until full agreement)
- **Usage:** Select in .skills.json, can choose different methodology
- **Status:**
  - [x] Design
  - [x] Deployment
  - [ ] Testing

---

### **development.server_development** (autonomous development)

#### 1. server_development_autonomous
- **Description:** Rule: no humans present, don't stop on questions
- **Rule:** Make decisions yourself, continue working
- **Use:** Server development without human (programmer) presence
- **Status:**
  - [x] Design
  - [x] Deployment
  - [ ] Testing

---

### **dev_main** (master project configuration)

#### 1. dev_config
- **Description:** Master configuration and global project settings
- **Configures:**
  - Development strategy (which methodology to use)
  - Branching mode (simple, etc)
  - Local development strategy
  - Autonomous mode (no humans present)
  - Operations (test, deploy, build, versioning, logging)
  - Which skills are enabled
- **Functions:** load_config, save_config, show_config, get_operation
- **Status:**
  - [x] Design
  - [x] Deployment
  - [ ] Testing

---

## 🔧 How to Use

### Enable/disable skills
```json
{
  "enabled_paths": [
    "development.common",
    "development.trello",
    "development.branching",
    "development.local_dev",
    "development.development_rules:methodology_three_stage",
    "development.server_development"
  ]
}
```

### Select different development methodology
Replace `methodology_three_stage` with another in config (when available).

---

## 🚀 Next Steps

- [ ] Implement dev_main (dev_config)
- [ ] Add specialized analyzers to project_analyzer (Django, Flask, React)
- [ ] Other development strategies (agile, waterfall)
- [ ] CI/CD integration
- [ ] Usage documentation

---

## 📝 Update History

| Date | Event |
|------|-------|
| 07.18.2026 | Restructuring: development_rules + server_development groups |
| 07.18.2026 | Moved workflow_state to development.trello |
| 07.18.2026 | Created development.development_rules with methodology_three_stage |
| 07.18.2026 | Created development.server_development with server_development_autonomous |
| 07.17.2026 | Implemented file_operations, branching_simple |
| 07.17.2026 | Created project_analyzer with 3-level analysis |
