# TODO — Portable Multi-Project MCP Server

План работы по спецификации из [tech.md](tech.md). Отмечайте `[x]` по мере выполнения.

## 0. Подготовка
- [x] Инициализировать локальный git-репозиторий
- [x] Выбрать стек: **Python** (Node.js-имена файлов из спеки → Python-эквиваленты)
- [x] Создать `.gitignore` (__pycache__, .venv, build, .git)
- [ ] Первый коммит скелета проекта

## 1. Структура репозитория (Python)
- [x] `pyproject.toml` + `requirements.txt`
- [x] `.skills.json.example` — пример конфигурации
- [x] `src/mcp_dev_skills/__init__.py`
- [x] `src/mcp_dev_skills/__main__.py` — точка входа, инициализация транспорта и жизненный цикл
- [x] `src/mcp_dev_skills/server.py` — инстанс MCP-сервера, регистрация тулов и роутинг запросов
- [x] `src/mcp_dev_skills/config.py` — обнаружение workspace и парсер `.skills.json`
- [x] `src/mcp_dev_skills/security.py` — резолв и валидация путей (sandbox)
- [x] `src/mcp_dev_skills/tools/project_analyzer.py`
- [x] `src/mcp_dev_skills/tools/file_operations.py`

## 2. Транспорт и изоляция
- [x] Подключить `stdio_server` (stdin/stdout)
- [x] Все пути резолвить относительно `Path.cwd()` или явно переданного клиентом
- [x] Убрать любые хардкод абсолютных путей (sandbox-first)

## 3. Dynamic Tool Discovery (feature flags)
- [x] При старте определять текущую рабочую директорию (`Path.cwd()`)
- [x] Искать файл `.skills.json` в этой директории
- [x] Если файла нет — регистрировать только безопасный read-only набор (`analyze_project_structure`)
- [x] Если файл есть — регистрировать только тулы из `enabled_skills`, исключая `disabled_skills`
- [x] При вызове отключённого тула возвращать явную ошибку:
      `"Tool [tool_name] is disabled by the current project's configuration (.skills.json)"`

## 4. Security Contract (Path Validation)
- [x] Утилита резолва и валидации путей
- [x] Каждый тул с аргументом-путём проверяет, что путь внутри workspace (`Path.cwd()`)
- [x] Детектить path escape (`../../etc/passwd`, `/etc/passwd`) — бросать ошибку и прерывать выполнение

## 5. Skill 1 — `analyze_project_structure`
- [x] Схема входа: `depth` (integer, default 3)
- [x] Рекурсивный обход workspace с уважением `.gitignore`
- [x] Игнорировать node_modules, build-артефакты, .git, venv
- [x] Строить лёгкое дерево ключевых файлов кода
- [x] Извлекать структурные подсказки (языки, конфиг-файлы)

## 6. Skill 2 — `safe_read_file`
- [x] Схема входа: `file_path` (string, required)
- [x] Чтение с проверками sandboxing
- [x] Интеграция с валидацией путей из раздела 4

## 7. Документация и приёмка
- [x] `README.md`: сборка/компиляция (`pip install -e .`)
- [x] `README.md`: настройка сервера в Claude Desktop (абсолютный путь до интерпретатора)
- [x] `README.md`: как создавать и использовать `.skills.json` в целевых проектах
- [x] Проверить критерии приёмки: код модульный, production-ready (smoke-тесты пройдены)
- [ ] Финальный коммит и push на GitHub

## Как проверялось
- Sandbox: `../../etc/passwd` и `/etc/passwd` отклоняются; `README.md` резолвится ✅
- Discovery без `.skills.json`: экспонируется только `analyze_project_structure` ✅
- Вызов отключённого тула → ошибка из спеки дословно ✅
- `analyze_project_structure` строит дерево + подсказки; `.venv`/`.git` игнорируются ✅
- `safe_read_file` читает файл внутри workspace ✅
