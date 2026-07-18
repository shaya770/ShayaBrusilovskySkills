"""Skill: server_development_autonomous — rules for autonomous server development.

When developing server WITHOUT human presence, apply these rules:
- No humans to ask questions to
- No reason to stop and wait for approval
- Make decisions autonomously
- Continue work uninterrupted

This is NOT a skill with actions/functions. This is a RULESET — instructions
for the AI to follow when working on server development in autonomous mode.
"""

from __future__ import annotations

from pathlib import Path

SKILL = {
    "name": "server_development_autonomous",
    "group": "development.server_development",
    "description": (
        "Ruleset for autonomous server development when no humans present. "
        "No one to ask, no reason to stop. Make decisions yourself, continue working. "
        "Instructions only — apply these rules when developing server independently."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


RULES = """\
# Autonomous Server Development Rules

Apply these rules when developing server WITHOUT human presence or ability to ask questions.

## Core Rule: No One To Ask, No Reason To Stop

**You are autonomous.** There is no human to consult, no one to wait for approval from.
Continue working without stopping.

---

## When You Encounter a Decision Point

### Instead of asking "What should I name this endpoint?"
→ Choose a logical, descriptive name yourself
  Example: `/api/v1/users/{id}` instead of asking

### Instead of asking "Which approach should I use?"
→ Choose the best approach based on the codebase and context
  Example: Use existing patterns, follow conventions, pick proven solutions

### Instead of asking "Should I commit this?"
→ Commit and push automatically when work is complete
  Example: Write tests, verify they pass, commit with meaningful message, push

### Instead of asking "Should I deploy?"
→ Deploy automatically when ready (if deployment is enabled)
  Example: Build, test, deploy to staging/production following configured pipeline

### Instead of asking "Is this code review ready?"
→ Review your own code against quality standards
  Example: Check tests pass, code follows conventions, no obvious bugs

---

## Guidelines for Autonomous Decision Making

1. **Use conventions:** Follow existing patterns in the codebase
2. **Be consistent:** Match style of surrounding code
3. **Document decisions:** Leave a comment explaining non-obvious choices
4. **Test thoroughly:** Write tests before committing
5. **Fail safely:** If uncertain, choose conservative approach

---

## When Something Goes Wrong

- Don't stop and ask for help
- Try alternative approaches
- Rollback if needed and retry
- Log what you tried and why it failed
- Continue working with next approach

---

## Your Autonomy Is a Feature, Not a Bug

Autonomous work means:
- Faster iteration (no waiting for responses)
- More experimentation (try multiple approaches)
- Better problem-solving (learn from failures)
- Uninterrupted flow (no context switches)

**Use it.**
"""


def execute(workspace_root: Path, **kwargs) -> str:
    """Return the autonomous server development ruleset."""
    return RULES
