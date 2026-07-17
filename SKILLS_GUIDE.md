# Trello Skills Guide

This document describes all Trello integration skills and how to use them.

## Quick Start

### 1. Configure Trello

```
configure_trello(board_url, api_key, token, scope="default", tech_level=1)
```

**Parameters:**
- `board_url`: Full Trello board URL
- `api_key`: Your Trello API key (from https://trello.com/app-key)
- `token`: Your Trello API token
- `scope`: Application/project scope (optional, default="default")
  - Examples: `"rental"`, `"crm"`, `"clinic"`, `"tasker"`
  - Allows multiple boards in one project
- `tech_level`: User's technical level (optional, default=1)
  - `0` = Non-technical (skip all technical questions)
  - `1` = Beginner
  - `2` = Intermediate
  - `3` = Expert

**What it does:**
- Validates Trello API credentials
- Fetches board details
- Auto-creates missing columns: Inbox, Planning, Approved, In Progress, Review, Done
- Saves config to `.claude/trello.json` with scope, tech_level, and detected language
- Each scope can have different tech_level settings

**Examples:**

Set up board for rental app (non-technical user):
```python
configure_trello(
    "https://trello.com/b/68f67984d4331f5a481236bf/rental-tasks",
    "your_api_key",
    "your_token",
    scope="rental",
    tech_level=0
)
```

Set up board for CRM (intermediate user):
```python
configure_trello(
    "https://trello.com/b/48e67984d4331f5a481236bf/crm-tasks",
    "your_api_key",
    "your_token",
    scope="crm",
    tech_level=2
)
```

**Run this first** to set up the board and configure tech level and scope.

### 1b. Switch Scope

```
switch_scope()               # List all configured scopes
switch_scope(scope="rental") # Switch to rental app's board
```

**What it does:**
- Lists all configured Trello scopes
- Shows which scope is currently active (marked with "current")
- Switches active scope (updates `current_scope` in config)
- All subsequent Trello skills use the active scope

**Example:**

List all scopes:
```python
switch_scope()
# Output:
# Available Trello scopes:
#   default
#     Board: General Tasks
#     Tech level: beginner
#
#   rental (current)
#     Board: Rental App Tasks
#     Tech level: non-technical
#
#   crm
#     Board: CRM Tasks
#     Tech level: intermediate
```

Switch to CRM board:
```python
switch_scope(scope="crm")
# Output:
# ✓ Switched to scope: 'crm'
#
# Board: CRM Tasks
# Tech level: intermediate
# Language: auto
```

**Use when:** Working on a different app/project in the same workspace.

## Workflow Skills (Smart & High-Level)

These skills embed workflow rules — use these instead of low-level operations.

### set_plan — Write Plan with Auto-Backup

```
set_plan(card_id, plan)
```

**Automatically:**
1. Detects task language (Russian/English/mixed)
2. Saves original task description to comment (one-time only)
3. Writes plan to card description (on same language as task)
4. Tags card with 'plan' label
5. Stores detected language in config

**Why this matters:** 
- Original task is preserved in comments so you can always refer back to it
- Plan language matches task language automatically (no manual translation needed)
- For Russian tasks → plan in Russian; for English tasks → plan in English

**Example:**
```python
# Task was: "Реализовать авторизацию через OAuth"
# You write plan in Russian:
set_plan(card_id, "Шаг 1: настроить OAuth провайдер...")
# → Language auto-detected as 'ru', stored in config
```

### ask_questions — Create Q&A Checklists

```
ask_questions(card_id, questions)
```

**Automatically:**
1. Loads user's tech_level from config
2. Filters questions based on tech_level
3. Creates 'Questions' checklist with filtered questions
4. Creates empty 'Answers' checklist (user fills in)
5. Moves card to Planning

**Tech-Level Filtering:**
- **tech_level=0** (non-technical): Skips all technical questions
  - Keeps: "When?", "Why?", "Budget?", "Deadline?"
  - Removes: "What language?", "Database?", "Performance?"
- **tech_level=1-3**: All questions included

**Usage:**
```python
# User is non-technical (tech_level=0)
ask_questions(card_id, [
    "1) What is the goal?",           # ← kept
    "2) Deadline?",                    # ← kept
    "3) What programming language?",   # ← SKIPPED (technical)
    "4) Database requirements?"        # ← SKIPPED (technical)
])
# Output: "Created 'Questions' checklist with 2 question(s)
#          (skipped 2 technical questions — user level: non-technical)"
```

**Matching:** Questions and answers are matched by number (e.g., "1) ..." → "1) ...").

### change_status — Move Card with Validation

```
change_status(card_id, new_status)
```

**Validates workflow rules:**
- ✓ Claude can: Inbox→Planning, Approved→In Progress, In Progress→Review
- ✓ User can: Planning→Approved, Review→Done

**Prevents accidental moves:**
- Cannot move to Approved (user decision)
- Cannot move to Done (user decision)
- Returns clear error if transition invalid

**Usage:**
```python
# Start work
change_status(card_id, "In Progress")  # OK: Approved→In Progress

# Finish work
change_status(card_id, "Review")  # OK: In Progress→Review

# This will fail (user decision):
# change_status(card_id, "Approved")  # Error: user must approve
```

## Atomic Skills (Low-Level Operations)

Use only when smart skills don't fit. Prefer smart skills.

### monitor_trello_board — Watch for Work

```
monitor_trello_board()
```

**Behavior:**
- Polls board every 3 seconds silently
- Prints nothing when NO work found
- When work found, outputs:
  ```
  WORK found:
    [Approved] Card 1: Task name
    [Inbox] Card 2: Another task
  After completing work, run the skill again: monitor_trello_board()
  ```

**Golden rule:** Run this in a loop during your work session to stay aware of incoming tasks.

### get_card — Read Card Details

```
get_card(card_id)
```

Returns:
- Name
- Description
- Labels
- All checklists (with checkbox states)
- Comments

### add_comment — Add Note to Card

```
add_comment(card_id, text)
```

Claude comments automatically get `🤖 ` prefix to distinguish from user comments.

### move_card — Move Between Columns (Deprecated)

```
move_card(card_id, list_name)
```

⚠️ **Prefer `change_status()` instead.** This skill bypasses workflow validation.

### create_checklist — Create Empty Checklist

```
create_checklist(card_id, name)
```

Creates named checklist (e.g., "Tasks", "Review points").

Returns checklist ID for use with `add_checklist_item()`.

### add_checklist_item — Add Item to Checklist

```
add_checklist_item(checklist_id, text)
```

Adds single item. For bulk operations, use `ask_questions()` instead.

### update_card_description — Update Description (Deprecated)

```
update_card_description(card_id, plan)
```

⚠️ **Prefer `set_plan()` instead.** This skill doesn't auto-backup original task.

## Column Reference

| Column | When | Who Moves |
|---|---|---|
| Inbox | User adds raw task | User |
| Planning | Plan written, questions asked | Claude |
| Approved | User approves plan | User |
| In Progress | Claude starts work | Claude |
| Review | Claude finished, report ready | Claude |
| Done | User accepted result | User |

## Language Rules

- **Structure (English):** Column names, labels, checklist names (Inbox, Planning, Questions, Answers)
- **Content (Auto):** Plans, questions, answers match task language (Russian/English/mixed)

**Auto-Detection:**
- `set_plan()` detects task language automatically
- Stores language in config as `"language": "ru"` or `"language": "en"`
- You write plans in task language; no manual translation needed

Examples:
```
Task: "Реализовать авторизацию через OAuth"
  └─ Detected language: Russian
  └─ Your plan: "Шаг 1: создать OAuth приложение..." (in Russian)

Task: "Implement OAuth authentication"
  └─ Detected language: English
  └─ Your plan: "Step 1: Create OAuth app..." (in English)

Task: "Сделай login feature на английском" (Mixed)
  └─ Detected language: Mixed
  └─ Your plan: Can use both Russian and English freely
```

**Board Structure (always English):**
- Column: "Planning" (English)
- Checklist: "Questions" (English)
- Checklist: "Answers" (English)
- Label: "plan" (English)

**Content (matches task language):**
- Comment: "Есть три варианта решения:" (Russian) or "Three possible solutions:" (English)
- Question: "1) Срок сдачи?" (Russian) or "1) Deadline?" (English)

## Multiple Scopes (Apps) in One Workspace

You can manage multiple applications from one project:

```
Workspace: my-startup/
├── .claude/trello.json  (stores all 3 boards)
├── rental/              (Rental app code)
├── crm/                 (CRM app code)
└── clinic/              (Clinic app code)

Trello config:
  current_scope: "rental"
  boards:
    rental:  tech_level=0, language=ru
    crm:     tech_level=2, language=en
    clinic:  tech_level=1, language=ru
```

**Workflow:**

1. Working on rental app:
   ```python
   switch_scope(scope="rental")  # Use rental board
   ask_questions(card_id, [...]) # No tech questions (tech_level=0)
   ```

2. Switch to CRM:
   ```python
   switch_scope(scope="crm")      # Use CRM board
   ask_questions(card_id, [...]) # Tech questions allowed (tech_level=2)
   ```

3. Check all scopes:
   ```python
   switch_scope()  # Lists all configured boards
   ```

Each scope has its own:
- Trello board (different board_id/board_url)
- Tech level (e.g., rental=0, crm=2)
- Detected language (e.g., rental=ru, crm=en)

## Card Lifecycle Example

```
1. User adds task to Inbox
2. Claude: set_plan(card_id, "Вот мой план...")
   → Moves card to Planning
   → Saves original task to comment
3. Claude: ask_questions(card_id, ["1) Сроки?", "2) Бюджет?"])
   → Creates Questions/Answers checklists
4. User: Answers questions + moves card to Approved
5. Claude: change_status(card_id, "In Progress")
6. Claude: ... does work ...
7. Claude: add_comment(card_id, "Готово. Проверь результат.")
8. Claude: change_status(card_id, "Review")
9. User: Reviews + moves card to Done
```

## Configuration

### Enable Skills

The `.skills.json` file controls which skills are enabled:

```json
{
  "enabled_paths": [
    "development.common",
    "development.trello"
  ],
  "disabled_skills": []
}
```

### Trello Setup (.claude/trello.json)

After running `configure_trello()`, your config stores multiple boards:

```json
{
  "api_key": "your_key_here",
  "token": "your_token_here",
  "current_scope": "rental",
  "boards": {
    "rental": {
      "board_id": "68f67984d4331f5a481236bf",
      "board_url": "https://trello.com/b/68f67984d4331f5a481236bf/rental-tasks",
      "board_name": "Rental App Tasks",
      "tech_level": 0,
      "language": "ru"
    },
    "crm": {
      "board_id": "48e67984d4331f5a481236bf",
      "board_url": "https://trello.com/b/48e67984d4331f5a481236bf/crm-tasks",
      "board_name": "CRM Tasks",
      "tech_level": 2,
      "language": "en"
    }
  }
}
```

**Top-level fields:**
- `api_key` and `token`: Shared Trello credentials (used for all scopes)
- `current_scope`: Which board is active (e.g., "rental")
- `boards`: Object with one entry per configured scope

**Per-scope fields:**
- `board_id`, `board_url`, `board_name`: Trello board info
- `tech_level` (set during configure_trello):
  - `0` = Non-technical user (no tech questions, only business/user questions)
  - `1` = Beginner (simple tech questions allowed)
  - `2` = Intermediate (moderate tech depth)
  - `3` = Expert (all questions, no filtering)
- `language` (auto-detected from task):
  - `"ru"` = Russian (detected if >70% Cyrillic)
  - `"en"` = English (detected if <10% Cyrillic)
  - `"mixed"` = Mixed language
  - `"auto"` = Not yet detected

## API Credentials

Store Trello credentials in `.claude/trello.env` (never commit):

```
TRELLO_API_KEY=your_key
TRELLO_TOKEN=your_token
TRELLO_BOARD_URL=https://trello.com/b/BOARD_ID/name
```

Get credentials from: https://trello.com/app-key

## Technical Level Guide

### What is "Technical Level"?

It determines what kind of questions Claude asks. Set once during `configure_trello()`.

| Level | Who | Questions Asked |
|---|---|---|
| **0** | Non-technical | Deadline? Budget? Goals? Success criteria? Who approves? |
| **1** | Beginner | Above + simple tech (Framework? Language?) |
| **2** | Intermediate | Above + moderate tech (Performance? Scalability?) |
| **3** | Expert | All possible questions, maximum depth |

### Tech Question Keywords

Claude detects technical questions by keywords:

**Russian:** язык, программирование, код, алгоритм, бд, sql, api, фреймворк, production

**English:** code, programming, database, sql, api, framework, performance, architecture, caching

If a question contains any of these, it's flagged as "technical" and may be skipped for non-technical users.

### Changing Tech Level

Current tech_level is in `.claude/trello.json`. To change:

```python
# Option 1: Reconfigure
configure_trello(board_url, api_key, token, tech_level=2)

# Option 2: Manually edit .claude/trello.json
{
  "tech_level": 2  # ← change this
}
```

## Troubleshooting

**"Error: Trello not configured"**
- Run `configure_trello()` first with valid URL, key, and token

**"Error: Card not found"**
- Verify card_id is correct (16-char hex string)
- Card may have been deleted

**"Error: Failed to create checklist"**
- Check that card exists and you have board permissions

**"Cannot move to Approved"**
- This is intentional. Only user can approve (workflow rule).
- User should move card to Approved in Trello UI.

**Emoji (🤖) not showing**
- UTF-8 encoding issue. Comments are stored correctly, may display incorrectly in some clients.

## Smart vs Atomic

**Use Smart Skills for:** Complete workflow steps (entire "planning" or "start work" step)
**Use Atomic Skills for:** Individual operations or when smart skill doesn't fit

**Smart Skills:**
- Enforce workflow rules
- Auto-perform related operations
- Simpler to use (fewer steps)

**Example — Planning a task:**
```python
# WRONG (manual, error-prone)
create_checklist(card_id, "Questions")
add_checklist_item(questions_cl, "1) What?")
add_checklist_item(questions_cl, "2) When?")
move_card(card_id, "Planning")

# RIGHT (smart skill, one call)
ask_questions(card_id, ["1) What?", "2) When?"])
```
