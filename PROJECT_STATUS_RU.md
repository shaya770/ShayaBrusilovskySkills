# mcp-dev-skills — Статус проекта

**Последнее обновление:** 2026-07-26 (Фаза A)  
**Статус:** Ядро usable; скиллы дозревают; Trello — LEGACY/FROZEN  

---

## North star

Портативная MCP-библиотека **умных developer-skills**: инструменты и правила разработки.  
Прикрутил к проекту через `.skills.json` → агент работает по твоей инженерной дисциплине.

Это **не** продукт про Trello. Board-pack остаётся в коде как optional frozen, по умолчанию выключен.

---

## Фаза A (сделано)

- [x] Документация приведена к реальной цели (README, статусы, example config)
- [x] Core-тесты: `security`, `config`, `loader`
- [x] `development.trello` выключен в default-конфигах (код сохранён)
- [x] Зафиксированы типы: tools / rulesets / legacy pack

## Дальше (Фаза B+)

- [ ] Довести `project_analyzer` / `file_operations` (поведение + тесты)
- [ ] UX ruleset’ов (когда агент должен читать methodology/local_dev)
- [ ] `dev_main` vs `.skills.json` — один source of truth
- [ ] CI: pytest на PR
- [ ] Безопасность branching (dry-run / confirm), если pack остаётся активным

---

## Инвентарь скиллов

### Core / recommended

| Path | Skills | Тип | Заметки |
| --- | --- | --- | --- |
| `development.common` | `project_analyzer`, `file_operations`, `setup_skills` | tools | Default без `.skills.json` |
| `development.development_rules` | `methodology_three_stage` | ruleset | |
| `development.local_dev` | `local_dev_default` | ruleset | |
| `development.branching` | `branching_simple` | tool | Опасно (merge/push) |
| `development.server_development` | `server_development_autonomous` | ruleset | |

### LEGACY / FROZEN (не включён по умолчанию)

| Path | Skills | Заметки |
| --- | --- | --- |
| `development.trello` | `trello`, `workflow_state` | Board polling; path только если реально нужен |

---

## Рекомендуемый `.skills.json`

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

Чтобы снова включить Trello — добавь `"development.trello"` в `enabled_paths` (код на месте).

---

## Архитектура (готово)

- [x] Иерархическое обнаружение (dot-notation + wildcards)
- [x] Динамический loader
- [x] Feature flags через `.skills.json`
- [x] Sandbox путей
- [x] MCP stdio server
- [x] Interactive setup CLI

---

## История

| Дата | Событие |
| --- | --- |
| 2026-07-26 | Фаза A: docs truth, core tests, Trello frozen |
| 2026-07-18 | development_rules + server_development; workflow_state → trello |
| 2026-07-17 | file_operations, branching_simple, project_analyzer |
