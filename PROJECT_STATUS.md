# mcp-dev-skills — Project status

**Last update:** 2026-07-26 (Phase A)  
**Status:** Core usable; skills maturing; Trello pack LEGACY/FROZEN  

---

## North star

Portable MCP skill library that encodes **smart development practice** (tools + rules).  
Attach to a project via `.skills.json` → agent works with your engineering discipline.

Not a Trello product. Board pack exists as optional frozen code only.

---

## Phase A (done)

- [x] Docs aligned with real goal (README, status, example config)
- [x] Core tests: `security`, `config`, `loader`
- [x] `development.trello` disabled in default configs (code kept)
- [x] Skill kinds documented: tools vs rulesets vs legacy pack

## Next (Phase B+)

- [ ] Harden `project_analyzer` / `file_operations` (behavior + tests)
- [ ] Clarify ruleset load UX (when agent should call methodology/local_dev)
- [ ] Resolve `dev_main` vs `.skills.json` (single source of truth)
- [ ] CI: pytest on PR
- [ ] Branching safety (dry-run / confirm) if kept active

---

## Skill inventory

### Core / recommended

| Path | Skills | Kind | Notes |
| --- | --- | --- | --- |
| `development.common` | `project_analyzer`, `file_operations`, `setup_skills` | tools | Default when no `.skills.json` |
| `development.development_rules` | `methodology_three_stage` | ruleset | |
| `development.local_dev` | `local_dev_default` | ruleset | |
| `development.branching` | `branching_simple` | tool | High blast radius (merge/push) |
| `development.server_development` | `server_development_autonomous` | ruleset | |

### LEGACY / FROZEN (not enabled by default)

| Path | Skills | Notes |
| --- | --- | --- |
| `development.trello` | `trello`, `workflow_state` | Board polling pack; re-enable path only if needed |

---

## Recommended `.skills.json`

```json
{
  "enabled_paths": [
    "development.common",
    "development.branching",
    "development.local_dev",
    "development.development_rules",
    "development.server_development"
  ],
  "disabled_skills": []
}
```

---

## Architecture (done)

- [x] Hierarchical discovery (dot-notation + wildcards)
- [x] Dynamic loader
- [x] `.skills.json` feature flags
- [x] Path sandbox
- [x] MCP stdio server
- [x] Interactive setup CLI

---

## Changelog (recent)

| Date | Event |
| --- | --- |
| 2026-07-26 | Phase A: docs truth, core tests, Trello frozen/out of default config |
| 2026-07-18 | development_rules + server_development groups; workflow_state under trello |
| 2026-07-17 | file_operations, branching_simple, project_analyzer |
