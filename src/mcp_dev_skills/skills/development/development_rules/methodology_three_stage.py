"""Skill: methodology_three_stage — three-stage development system for ShayaBrusilovskySkills.

Development strategy: Design → Deployment → Testing
Each stage is tracked independently and marked complete when ready.

Includes: Step-by-Step Discussion Protocol (one point at a time until full agreement).
"""

from __future__ import annotations

from pathlib import Path

SKILL = {
    "name": "methodology_three_stage",
    "group": "development.development_rules",
    "description": (
        "Three-stage development system for ShayaBrusilovskySkills project. "
        "Stages: Design (проектирование), Deployment (развертывание), Testing (тестирование). "
        "Includes Step-by-Step Discussion Protocol: discuss one point at a time until full agreement. "
        "Enable via .skills.json if this is your development strategy."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


METHODOLOGY = """\
# Three-Stage Development Methodology

Universal system for tracking development progress on ANY feature, module, skill,
or system. Language-agnostic, project-agnostic, scope-agnostic.

## Three Stages

### Stage 1: Проектирование (Design)
**Goal:** Understand requirements, design the solution, make decisions.

**Activities:**
- Clarify what needs to be built and why
- Sketch architecture, API, interfaces
- List assumptions and constraints
- Identify edge cases and failure modes
- Make all design decisions (technology, approach, patterns)
- Document the plan

**Completion criteria:**
- Design is documented and reviewed
- No major design questions remain unanswered
- Ready to start building

**Marks completion when:** "я больше не хочу ничего менять в дизайне"

---

### Stage 2: Развертывание (Deployment)
**Goal:** Implement the design, make it work, deploy it.

**Activities:**
- Write code / build the system to spec
- Implement all planned features
- Fix bugs found during implementation
- Deploy to target environment (local, staging, production)
- Ensure the system runs without critical issues
- Document how to use / configure

**Completion criteria:**
- Code is written and deployed
- Core functionality works as designed
- No blocking bugs in main workflow
- Ready for user testing

**Marks completion when:** "я больше не хочу ничего деплоить"

---

### Stage 3: Тестирование (Testing)
**Goal:** Verify everything works, catch edge cases, ensure quality.

**Activities:**
- Run manual tests (golden path + edge cases)
- Write automated tests if applicable
- Test error handling and recovery
- Test performance, security, reliability
- Collect feedback from early users
- Fix bugs found during testing
- Performance tuning if needed

**Completion criteria:**
- All planned tests pass
- No known critical bugs
- Edge cases are handled
- Performance is acceptable
- User feedback is positive

**Marks completion when:** "тестирование законченно, можно в продакшен"

---

## How to Use

### Track a single feature
```
✓ Проектирование (done)
✓ Развертывание (done)
⏳ Тестирование (in progress)
```

### Update status
When a stage is complete:
1. Change `[ ]` to `[x]` in your tracking file
2. Commit the change (optional, but recommended)
3. Start the next stage

### Mark multiple items
```markdown
# Feature: OAuth Integration

**Stage statuses:**
- [x] Проектирование
- [x] Развертывание
- [ ] Тестирование

**Design decisions:**
- Use OAuth 2.0 with PKCE
- Store tokens in HttpOnly cookies
- Refresh tokens every 1 hour

**Deployment status:**
- Backend endpoints implemented
- Frontend integration complete
- Database schema ready

**Testing plan:**
- [ ] Manual login/logout flow
- [ ] Token refresh on expiry
- [ ] Error handling (invalid token, etc.)
- [ ] Security audit needed
```

---

## Why Three Stages?

**Проектирование (Design):**
- Prevents "we didn't think about this" during coding
- Makes decisions visible and reviewable
- Catches architectural issues early
- Low cost to change (just a document)

**Развертывание (Deployment):**
- Separates "building it" from "testing it"
- Ensures feature is actually available
- Gives users something to test against
- Clear handoff point: "feature is ready for testing"

**Тестирование (Testing):**
- Verifies design assumptions actually work
- Catches bugs and edge cases
- Ensures user experience is good
- Clear gate before production

---

## Step-by-Step Discussion Protocol

**Within each stage, follow this workflow:**

1. **Present ONE item/decision/plan** — don't overwhelm with everything at once
2. **Discuss it thoroughly** — answer questions, explain reasoning, address concerns
3. **Wait for approval** — "это меня полностью устраивает" (full satisfaction) or equivalent
4. **Mark it done** — once approved, this item does NOT re-raise in future iterations
5. **Move to next item** — proceed with the next point only after current is closed

**Why this works:**
- Each decision gets full attention and clarity
- No surprises or misalignments later
- Approved items stay approved (no backtracking)
- Clear handoff: "done, move on" vs. "needs more work"

**Example workflow:**

```
Claude: "Пункт 1: Используем PostgreSQL локально вместо SQLite"
  ↓
User: "Почему? Разница есть?"
  ↓
Claude: [explains pros/cons, local vs. prod consistency]
  ↓
User: "Ладно, это меня устраивает"
  ↓
✓ Decision locked. Never re-discuss unless explicitly re-opened.

Claude: "Пункт 2: Пароли тестовых пользователей = их имена"
  ↓
User: [discussion/changes if needed]
  ↓
User: "Согласен, идем дальше"
  ↓
✓ Next item begins.
```

**Approved items are FINAL for that stage:**
- Don't bring them up again during the same stage
- Don't re-litigate them in the next stage
- Only revisit if user explicitly asks ("давай вернёмся к...")

---

## Common Mistakes to Avoid

❌ **Don't skip design.** "We'll design it as we code" = rework, bugs, wasted time.

❌ **Don't test during deployment.** "Let's test while building" = scope creep, unclear status.

❌ **Don't leave testing to the end.** Testing reveals design flaws that are expensive to fix.

✅ **Do keep stages independent.** Each stage has a clear goal and exit criteria.

✅ **Do mark stages complete.** Gives clarity on what's done vs. what's next.

✅ **Do revisit earlier stages if needed.** Bugs found in testing may require design changes—that's OK. Restart that stage.

---

## Apply to Anything

This system works for:
- Single features (OAuth, caching, metrics)
- Entire modules (payments, authentication, reports)
- Skills and tools (MCP servers, CLI commands)
- Bug fixes (design the fix, deploy it, test it)
- Refactoring (design the new structure, deploy it, test it)

The stages scale up or down depending on scope.

---

## Quick Reference

| Stage | Time | Output | Next Step |
|-------|------|--------|-----------|
| Проектирование | Plan, design, decide | Document | Build |
| Развертывание | Implement, deploy | Working system | Test |
| Тестирование | Test, fix, verify | Quality assurance | Ship |

"""


def execute(workspace_root: Path, **kwargs) -> str:
    """Return the three-stage development methodology."""
    return METHODOLOGY
