# Trello Skills Guide

> **LEGACY / FROZEN**  
> This pack (`development.trello`) is **not enabled by default**.  
> Code remains under `src/mcp_dev_skills/skills/development/trello/` for optional
> re-enable: add `"development.trello"` to `.skills.json` → `enabled_paths`.  
> North star of this repo is **smart development skills & rules**, not board polling.

All Trello operations live in **one skill: `trello`**, dispatched by the `action` parameter.
Workflow rules are enforced in code — there is no low-level bypass path.

## Quick Start

### 1. Configure a board

```python
trello(action="configure",
       board_url="https://trello.com/b/BOARD_ID/name",
       api_key="...", token="...",
       scope="rental", tech_level=0)
```

**Parameters:**
- `board_url`: Full Trello board URL
- `api_key` / `token`: From https://trello.com/app-key
- `scope`: Application/project scope (optional, default `"default"`). Examples: `"rental"`, `"crm"`, `"clinic"`. Allows multiple boards in one workspace.
- `tech_level`: 0=non-technical, 1=beginner, 2=intermediate, 3=expert (optional, default 1). Affects question filtering.

**What it does:**
- Validates credentials, fetches board details
- Auto-creates missing columns: Inbox, Planning, Approved, In Progress, Review, Done
- Saves config to `.claude/trello.json` (gitignored — credentials never reach git)

### 2. Switch scope / register planned apps

```python
trello(action="switch_scope")                              # list all scopes
trello(action="switch_scope", scope="crm")                 # switch active board
trello(action="switch_scope", mark_known="rental,crm")     # register planned apps
```

Status symbols: `✓` configured, `○` known/planned, `← current` active.

### 3. Check for work

**One-shot check** (on demand):

```python
trello(action="check_board")
# → "🚨 WORK FOUND: [Approved] Fix login (id: ...)"  or  "No work found in Inbox/Approved."
```

Returns instantly — no polling inside the tool. Cards labeled `wait` are skipped.

**Continuous monitoring** (zero tokens while idle) — launch the monitor script
as a **background process** (Claude: run it via your shell in background mode):

```bash
python -m mcp_dev_skills.monitor --workspace <path> --interval 30
```

How it works: the script polls Trello silently and prints **nothing** while there
is no work — so the background runner stays quiet and Claude is never woken up
(no tokens burned on idle checks). The moment actionable cards appear, it prints
them and **exits** — that output wakes Claude, who reads the card list and starts
working. After finishing, relaunch the monitor. Never run this loop inside an MCP
tool call — it would block the server and hit the client timeout.

## Workflow Actions (rules built in)

### set_plan — write plan with auto-backup

```python
trello(action="set_plan", card_id="...", plan="Шаг 1: ...")
```

Automatically: detects task language (ru/en/mixed), saves original description to a
comment (one-time backup), writes the plan to the description, stores the language in
the scope config. Write the plan in the task's language.

### ask_questions — Q&A checklists with tech-level filter

```python
trello(action="ask_questions", card_id="...",
       questions=["1) What is the goal?", "2) Deadline?", "3) What database?"])
```

Automatically: loads `tech_level` from the current scope, filters out technical
questions for `tech_level=0`, creates a "Questions" checklist and an empty "Answers"
checklist, moves the card to Planning. Questions and answers are matched by number.

### change_status — move card with validation

```python
trello(action="change_status", card_id="...", new_status="In Progress")
```

| Transition | Allowed for |
|---|---|
| Inbox → Planning | Claude |
| Planning → Approved | **User only** |
| Approved → In Progress | Claude |
| In Progress → Review | Claude |
| Review → Done | **User only** |

Attempts to move to Approved/Done return a clear error — approval is always a human decision.

## Read & Write Actions

```python
trello(action="get_card", card_id="...")                     # full details: desc, labels, checklists (with ids), comments
trello(action="add_comment", card_id="...", text="...")      # 🤖 prefix added automatically
trello(action="create_checklist", card_id="...", name="Review points")
trello(action="add_checklist_item", checklist_id="...", text="...")
```

## workflow_state — restore context in one call

```python
workflow_state()
```

Returns a single snapshot: current scope and board, cards in
Inbox/Planning/Approved/In Progress/Review (with ids), git branch, uncommitted file
count, and recent commits. Use it at the start of every session instead of poking
around with several calls.

## Branch-Per-Card Workflow (branching_simple)

```python
branching_simple(action="assign", card_id="...", branch_name="crm-auth-oauth", agent_id="claude")
# → git branch created from main, Trello comment added, card → In Progress

branching_simple(action="update_status", card_id="...")
# → reads commits on the branch, posts progress comment to Trello
# (branch name auto-detected from the earlier assign comment)

branching_simple(action="list", filter="crm-")
# → active branches with commit counts
```

## Card Lifecycle

```
1. User adds task to Inbox
2. Claude: trello(action="set_plan", ...)          → plan in description, original backed up
3. Claude: trello(action="ask_questions", ...)     → card → Planning, Q&A checklists
4. User: answers questions, moves card to Approved
5. Claude: trello(action="change_status", new_status="In Progress")
6. Claude: ... does the work ... (optionally branching_simple assign/update_status)
7. Claude: trello(action="add_comment", text="Готово. Проверь результат.")
8. Claude: trello(action="change_status", new_status="Review")
9. User: reviews, moves card to Done
```

## Language Rules

- **Structure (always English):** column names, labels, checklist names (Inbox, Planning, Questions, Answers)
- **Content (matches the task):** plans, questions, comments in the task's language

Detection: >70% Cyrillic → `ru`, <10% → `en`, otherwise `mixed`. Detected on
`set_plan` and stored per scope.

## Technical Level Guide

Set per scope during `configure`. Controls which questions `ask_questions` keeps:

| Level | Who | Questions asked |
|---|---|---|
| **0** | Non-technical | Deadline? Budget? Goals? Success criteria? |
| **1** | Beginner | Above + simple tech |
| **2** | Intermediate | Above + moderate tech |
| **3** | Expert | Everything, no filtering |

Technical questions are detected by keywords (язык, код, бд, api, фреймворк / code,
database, framework, performance, architecture, ...).

To change: re-run `configure` with a new `tech_level`, or edit
`.claude/trello.json` → `boards.<scope>.tech_level`.

## Multiple Scopes in One Workspace

```
Workspace: my-startup/
├── .claude/trello.json
│   known_scopes: [clinic, crm, rental]   ← all planned apps
│   current_scope: rental                 ← currently active
│   boards:
│     rental: configured (tech_level=0, language=ru)
│     crm:    configured (tech_level=2, language=en)
│     # clinic: known but not configured yet
├── rental/
├── crm/
└── clinic/
```

Each scope has its own board, tech level, and detected language. All actions operate
on the **current** scope; switch with `trello(action="switch_scope", scope="...")`.

## Configuration Files

### .skills.json (which skills are loaded)

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

### .claude/trello.json (runtime config, gitignored)

```json
{
  "api_key": "...",
  "token": "...",
  "current_scope": "rental",
  "known_scopes": ["clinic", "crm", "rental"],
  "boards": {
    "rental": {
      "board_id": "...",
      "board_url": "https://trello.com/b/.../rental-tasks",
      "board_name": "Rental App Tasks",
      "tech_level": 0,
      "language": "ru"
    }
  }
}
```

`api_key`/`token` are shared across scopes; everything else is per-board.
**Never commit this file** — it is in `.gitignore`.

Optional top-level field `"backend"` selects the board implementation
(default `"trello"`). The workflow code talks to a neutral `BoardBackend`
interface (`backend.py`) — when the own web interface replaces Trello,
a `WebBackend` gets registered there and this field switches to it;
skills, monitor, and branching stay untouched.

## Troubleshooting

Errors now carry the real HTTP status from Trello:

- **"Trello not configured"** — run `trello(action="configure", ...)` first
- **"Trello API 401 ... invalid API key or token"** — regenerate credentials at https://trello.com/app-key
- **"Trello API 404 ... not found"** — bad card/checklist id, or the token has no access to that board
- **"Trello API 429 ... rate limited"** — slow down; retry after a pause
- **"Cannot move to Approved/Done (user decision)"** — intentional workflow rule; the user moves these in the Trello UI
