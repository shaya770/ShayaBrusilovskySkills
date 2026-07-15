# TODO — Portable Multi-Project MCP Server

План работы по спецификации из [tech.md](tech.md). Отмечайте `[x]` по мере выполнения.

## 0. Подготовка
- [x] Инициализировать локальный git-репозиторий
- [x] Выбрать стек: **Python** (Node.js-имена файлов из спеки → Python-эквиваленты)
- [x] Создать `.gitignore` (__pycache__, .venv, build, .git)
- [x] Первый коммит скелета проекта

## 1. Структура репозитория (Python, иерархическая)
- [x] `pyproject.toml` + `requirements.txt`
- [x] `.skills.json.example` — пример конфигурации
- [x] Переделан путь `tools/` → `skills/` с вложенными папками
- [x] `src/mcp_dev_skills/__init__.py`
- [x] `src/mcp_dev_skills/__main__.py` — точка входа (сервер или CLI setup)
- [x] `src/mcp_dev_skills/server.py` — MCP-сервер, регистрация тулов, роутинг
- [x] `src/mcp_dev_skills/config.py` — парсер `.skills.json` (dot-notation paths)
- [x] `src/mcp_dev_skills/security.py` — резолв и валидация путей (sandbox)
- [x] `src/mcp_dev_skills/loader.py` — **динамическая загрузка скилов по path'ам**
- [x] `src/mcp_dev_skills/setup.py` — **интерактивная CLI для setup**
- [x] `src/mcp_dev_skills/skills/разработка/общее/*.py` — скиллы

## 2. Транспорт и изоляция
- [x] Подключить `stdio_server` (stdin/stdout)
- [x] Все пути резолвить относительно `Path.cwd()` или явно переданного клиентом
- [x] Убрать любые хардкод абсолютных путей (sandbox-first)

## 3. Dynamic Tool Discovery с иерархией и dot-notation
- [x] При старте определять текущую рабочую директорию (`Path.cwd()`)
- [x] Искать файл `.skills.json` в этой директории
- [x] Если файла нет — регистрировать только безопасный набор (`разработка.общее`)
- [x] Если файл есть — регистрировать только скиллы из `enabled_paths` (dot-notation)
- [x] Поддержка wildcard: `"разработка.*"` = все скиллы под разработкой
- [x] При вызове отключённого скилла возвращать явную ошибку

## 4. Security Contract (Path Validation)
- [x] Утилита резолва и валидации путей
- [x] Каждый скилл с аргументом-путём проверяет, что путь внутри workspace
- [x] Детектить path escape (`../../etc/passwd`, `/etc/passwd`) — бросать ошибку

## 5. Skill 1 — `analyze_project_structure`
- [x] Схема входа: `depth` (integer, default 3)
- [x] Рекурсивный обход workspace с уважением `.gitignore`
- [x] Игнорировать node_modules, build-артефакты, .git, venv
- [x] Строить лёгкое дерево ключевых файлов кода
- [x] Извлекать структурные подсказки (языки, конфиг-файлы)

## 6. Skill 2 — `safe_read_file`
- [x] Схема входа: `file_path` (string, required)
- [x] Чтение с проверками sandboxing
- [x] Интеграция с валидацией путей

## 7. Skill 3 — `setup_skills` (новый)
- [x] Действие `list_tree` — показать все доступные скиллы в формате дерева
- [x] Действие `generate_config` — создать `.skills.json` с выбранными path'ами

## 8. CLI Setup Утилита
- [x] `python -m mcp_dev_skills setup` — интерактивный выбор скилов
- [x] Показывает список всех доступных скилов с номерами
- [x] Пользователь вводит номера скилов или `all`/`none`
- [x] Генерирует `.skills.json` автоматически

## 9. Документация и приёмка
- [x] `README.md`: архитектура (иерархия скилов, dot-notation)
- [x] `README.md`: quick start (install, setup, config)
- [x] `README.md`: примеры конфигов (.skills.json для разных проектов)
- [x] `README.md`: как добавлять новые скиллы и группы
- [x] Код модульный, production-ready (smoke-тесты пройдены)
- [ ] Финальный коммит
- [ ] Push на GitHub (когда будет remote)

## Как проверялось
- Иерархия скилов загружается правильно
- `разработка.общее` загружает 3 скилла (analyze, read, setup) ✅
- Dot-notation работает (wildcards поддерживаются) ✅
- `.skills.json` генерируется корректно ✅
- CLI setup работает и сохраняет конфиг ✅
- Sandbox валидация работает ✅
