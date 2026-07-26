# TODO — Smart developer skills (MCP)

## Phase A: Foundation (DONE — 2026-07-26)
- [x] North-star docs (README, PROJECT_STATUS, example config)
- [x] Core tests: security, config, loader
- [x] Freeze Trello pack (disabled in default configs; code kept)
- [x] Document skill kinds: tools / rulesets / legacy

## Phase B: Common skills trust
- [ ] `project_analyzer` behavior tests + clearer level contract
- [ ] `file_operations` access-control tests + docs
- [ ] setup CLI: recommended defaults without Trello

## Phase C: Encode experience as rules
- [ ] methodology / local_dev / autonomous — polish + when-to-call guidance
- [ ] Optional: definition-of-done / review gates as rulesets

## Phase D: Hygiene
- [ ] Single config story (`dev_main` vs `.skills.json`)
- [ ] CI: pytest (+ ruff)
- [ ] Version/docs sync on release

## Legacy (frozen)
- [x] `development.trello` — optional board pack (not enabled by default)
- [ ] Do not invest unless actively used again

## How to verify Phase A
```bash
pip install -e .
pip install pytest
pytest
```
