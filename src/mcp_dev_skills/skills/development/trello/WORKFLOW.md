# Trello Task Workflow

Tasks are set and discussed in **Trello**. Claude reads and writes via REST API.

## Language Rules

- **Structure — English:** column names, labels, checklists (`❓ Questions`, `✍️ Answers`).
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

## Workflow Cycle

1. **Take task:** Check cards in `Inbox` (new) and `Approved` (ready).
2. **Write plan:** Save original desc in comment `🤖 Original task:` (one-time). Then write plan in Russian in desc.
3. **Ask questions (if needed):**
   - `❓ Questions` — points in Russian: `1) …`, `2) …`
   - `✍️ Answers` — empty checklist (user adds points)
4. **Wait for user:** They answer in `Answers` and/or move to `Approved`.
5. **Work:** Move to `In Progress`, execute, write brief report.
6. **Submit:** Move to `Review`. User reviews → `Done`.

## Conventions

- All Claude comments start with `🤖 `.
- Labels (English) = type/app (`rental`, `crm`, `clinic`, `tasker`) + helpers (`plan`, `urgent`, `bug`, `wait`).
- **`wait` = DON'T TOUCH.** Cards with `wait` label are skipped during board checks.

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
```

## Encoding (Critical!)

Cyrillic/Hebrew text cannot be sent as raw shell arguments.
- **Python:** `urllib.parse.urlencode({...}).encode("utf-8")`
- **curl:** via UTF-8 file with `--data-urlencode "desc=$(cat file)"`
