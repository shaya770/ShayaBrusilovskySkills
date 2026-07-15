# TODO — Portable Multi-Project MCP Server with Skill Hierarchy

План работы по спецификации из [tech.md](tech.md). Отмечайте `[x]` по мере выполнения.

## Phase 1: Architecture & Core (DONE)
- [x] Инициализировать локальный git-репозиторий
- [x] Выбрать стек: **Python**
- [x] Создать `.gitignore`
- [x] Рефакт структуры: `tools/` → `skills/` с вложенными папками (English)
- [x] Реализовать `loader.py` для динамической загрузки скилов по path'ам (dot-notation)
- [x] Добавить поддержку wildcard (`development.*`)
- [x] Обновить `config.py` (dot-notation paths вместо enabled_skills)
- [x] Обновить `server.py` (использовать loader)
- [x] Создать CLI setup утилиту (`python -m mcp_dev_skills setup`)

## Phase 2: Core Skills (DONE)
- [x] `analyze_project_structure` (development.common)
- [x] `safe_read_file` (development.common)
- [x] `setup_skills` (development.common)

## Phase 3: Trello Integration (DONE)
- [x] `check_trello_board` (development.trello)
- [x] WORKFLOW.md с документацией протокола Trello
- [x] Поддержка TRELLO_API_KEY и TRELLO_TOKEN из `.claude/trello.env`
- [x] Автоматический retry для Trello API
- [x] Поддержка auto_mode (пропуск Inbox-черновиков)

## Phase 4: Documentation & Polish (IN PROGRESS)
- [x] README.md: архитектура (иерархия скилов, dot-notation)
- [x] README.md: quick start (install, setup, config)
- [x] README.md: примеры конфигов (.skills.json)
- [x] README.md: как добавлять новые скиллы и группы
- [x] README.md: Trello интеграция
- [x] Обновлена структура скилов (только English пути)
- [ ] Финальный коммит

## Phase 5: Future Skills (TODO for later)
- [ ] `development.django` — анализ моделей, миграций, settings
- [ ] `development.frontend` — поиск компонентов, зависимостей
- [ ] `deployment.docker` — анализ Dockerfile, docker-compose
- [ ] `deployment.k8s` — парсинг K8s манифестов
- [ ] `ci-cd.*` — GitHub Actions, GitLab CI конфиги

## Как проверялось
- Иерархия скилов загружается правильно ✅
- `development.common` загружает 3 скилла ✅
- `development.trello` загружает 1 скилл (check_trello_board) ✅
- Dot-notation работает (wildcards поддерживаются) ✅
- `.skills.json` генерируется корректно ✅
- CLI setup работает ✅
- Sandbox валидация работает ✅
- Только English пути (русский только контент) ✅
