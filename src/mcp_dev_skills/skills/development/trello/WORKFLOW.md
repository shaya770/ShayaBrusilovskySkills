# Trello Task Workflow

Tasks are set and discussed in **Trello**. Claude reads and writes via REST API.

## Language Rules

- **Structure — English:** column names, labels, checklists (`Questions`, `Answers`).
- **Content — Russian:** descriptions (plans), comments, checklist text, questions/answers, all correspondence.

## Credentials & Board

- **Keys:** `TRELLO_API_KEY`, `TRELLO_TOKEN` in **`.claude/trello.env`** (in `.gitignore`, never commit).
- **API base:** `https://api.trello.com/1/`
- Each project has its own board ID.

### Example `.claude/trello.env`

```
TRELLO_API_KEY=your_key_here
TRELLO_TOKEN=your_token_here
```

## Board Columns (example)

| Column | Purpose |
|---|---|
| 📥 Inbox | Raw tasks from user |
| 📋 Planning | Plan written, awaiting answers/approval |
| ✅ Approved | Plan approved, ready to work |
| 🔨 In Progress | Claude is working |
| 👀 Review | Done, report in card, awaiting review |
| ✔️ Done | Accepted |

## Who Moves Cards (IMPORTANT)

- **User** moves card on decision: `Planning → Approved` (plan approved), `Review → Done` (accepted).
- **Claude** moves card on status change: `Inbox → Planning` (plan written), `Approved → In Progress` (started), `In Progress → Review` (finished).
- Claude never moves to Approved/Done — that's user's decision.

## Full Workflow Cycle

### 1. Take Task
User says "check board" (trigger). Look at:
- `Inbox` cards (new tasks)
- `Approved` cards (ready to work)
- `Planning` cards (awaiting answers)

### 2. Write Plan

**⚠️ CRITICAL: Save original task FIRST**

Before writing plan:
1. If description has text (task in desc) → copy to comment: `🤖 Original task:\n{text}` (one-time only)
2. Only then write plan **in Russian** in description
3. Now plan can be re-written safely (original is in comment)
4. Mark with label `plan`

If description empty (task in title only) — skip comment.

### 3. Ask Questions (if needed)

**TWO checklists (names English, content Russian):**
- `❓ Questions` — points in Russian: `1) …`, `2) …`, `3) …`
- `✍️ Answers` — EMPTY checklist. User adds points in same order with number: `1) …`, `2) …`

Match answer to question **by number at start of item** (not by position — user may answer selectively).

Move card to `📋 Planning`.

### 4. Wait for User
User answers in `Answers` checklist and/or moves card to `✅ Approved`.

### 5. Work
When in `Approved`:
- Move to `🔨 In Progress`
- Execute work (follow development rules: feature branch, tests before/after, etc.)

### 6. Submit
- Write brief report (comment or description update)
- Move to `👀 Review`
- User reviews → `✔️ Done`

## Conventions

- All Claude comments start with `🤖 ` to distinguish from user.
- Plan — in description; dialog — in checklists/comments; history stays in card.
- Labels (English) = type/app (`rental`, `crm`, `clinic`, `tasker`) + helpers (`plan`, `urgent`, `bug`, `wait`). Labels are NOT status.
- **`wait` = DON'T TOUCH.** Cards with `wait` label are skipped during board checks: don't write plan, don't ask questions, don't take into work — until user removes label.

## Skills Mapping to Workflow

**Smart Skills** (embed workflow rules):
- `set_plan(card_id, plan)` — Write plan, auto-save original to comment
- `ask_questions(card_id, questions_list)` — Create Questions/Answers checklists, move to Planning
- `change_status(card_id, new_status)` — Validate workflow rules, move card

**Basic Skills** (atomic operations):

| Workflow Step | Skill | Usage |
|---|---|---|
| Take task | `monitor_trello_board()` | Find WORK on board |
| | `get_card(card_id)` | Read full card details |
| Write plan | `set_plan(card_id, plan)` | Auto-save original, write plan |
| Ask questions | `ask_questions(card_id, questions)` | Auto-create checklists, move to Planning |
| Work | `change_status(card_id, "In Progress")` | Move to In Progress (validated) |
| | `add_comment(card_id, "text")` | Add progress comments |
| Submit | `add_comment(card_id, "report")` | Add final report |
| | `change_status(card_id, "Review")` | Move to Review (validated) |
| Repeat | `monitor_trello_board()` | Check board again |

**Legacy Skills** (kept for compatibility, better to use smart skills):
- `update_card_description(card_id, plan)` — Deprecated, use `set_plan`
- `create_checklist(card_id, name)` — Use with `add_checklist_item`
- `move_card(card_id, list_name)` — Deprecated, use `change_status`

## Key API Endpoints

```
# Cards in column
GET  /lists/{listId}/cards?fields=name,desc,labels,idList

# Card details
GET  /cards/{cardId}?fields=name,desc,labels,idList

# Card checklists
GET  /cards/{cardId}/checklists

# Add comment
POST /cards/{cardId}/actions/comments?text=...

# Move card
PUT  /cards/{cardId}?idList={listId}

# Update description
PUT  /cards/{cardId}?desc=...

# Create checklist
POST /cards/{cardId}/checklists?name=...

# Add checklist item
POST /checklists/{checklistId}/checkItems?name=...
```

## Encoding (Critical!)

Cyrillic/Hebrew text cannot be sent as raw shell arguments.
- **Python:** `urllib.parse.urlencode({...}).encode("utf-8")`
- **curl:** via UTF-8 file with `--data-urlencode "desc=$(cat file)"`
