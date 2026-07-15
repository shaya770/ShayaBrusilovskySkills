# Trello Skills Guide

This document describes all Trello integration skills and how to use them.

## Quick Start

### 1. Configure Trello

```
configure_trello(board_url, api_key, token)
```

- Validates Trello API credentials
- Fetches board details
- Auto-creates missing columns: Inbox, Planning, Approved, In Progress, Review, Done
- Saves config to `.claude/trello.json`

**Run this first** to set up the board.

## Workflow Skills (Smart & High-Level)

These skills embed workflow rules — use these instead of low-level operations.

### set_plan — Write Plan with Auto-Backup

```
set_plan(card_id, plan)
```

**Automatically:**
1. Saves original task description to comment (one-time only)
2. Writes plan to card description
3. Tags card with 'plan' label

**Why this matters:** Original task is preserved in comments so you can always refer back to it.

### ask_questions — Create Q&A Checklists

```
ask_questions(card_id, questions)
```

**Automatically:**
1. Creates 'Questions' checklist with numbered items
2. Creates empty 'Answers' checklist (user fills in)
3. Moves card to Planning

**Usage:**
```python
ask_questions(card_id, [
    "1) What is the exact goal?",
    "2) Any edge cases to consider?",
    "3) Performance requirements?"
])
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

- **Structure (English):** Column names, labels, checklist names
- **Content (Russian):** Plans, questions, answers, comments, all correspondence

Example:
- Column: "Planning" (English)
- Comment: "Есть три варианта решения:" (Russian)
- Label: "plan" (English)

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

Add "development.trello" to enabled_paths to enable all Trello skills.

## API Credentials

Store Trello credentials in `.claude/trello.env` (never commit):

```
TRELLO_API_KEY=your_key
TRELLO_TOKEN=your_token
TRELLO_BOARD_URL=https://trello.com/b/BOARD_ID/name
```

Get credentials from: https://trello.com/app-key

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
