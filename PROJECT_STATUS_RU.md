# ShayaBrusilovskySkills — Статус проекта и инвентарь скиллов

**Обновлено:** 2026-07-17
**Статус:** Ядро готово; Trello консолидирован в один скилл

---

## 📊 Обзор проекта

MCP-сервер (Model Context Protocol) с иерархической библиотекой **скиллов разработчика** для управления мультипроектной разработкой через **Trello** и **git-ветки**, с гибкой конфигурацией на каждый проект.

**Всего скиллов:** 8 (в 4 группах)

---

## 🎯 Что сделано

### ✅ Архитектура ядра
- [x] Иерархическое обнаружение скиллов через dot-notation пути (`development.trello`)
- [x] Динамический загрузчик с wildcard (`development.*`)
- [x] Конфигурация через `.skills.json` (`enabled_paths`)
- [x] Песочница путей (валидация, изоляция workspace)
- [x] MCP-сервер поверх stdio
- [x] Единый Trello HTTP-клиент (`trello_api.py`) с настоящими ошибками (401/404/429 различаются)
- [x] Scope-aware конфиг везде (`config_utils.py`) — плоский формат больше нигде не читается

### ✅ Консолидация 2026-07-17
- [x] 12 отдельных Trello-скиллов слиты в **один скилл `trello`** с параметром `action`
- [x] `monitor_board` (бесконечный цикл — блокировал MCP-сервер) заменён на одноразовый `check_board` + отдельный фоновый монитор (`src/mcp_dev_skills/monitor.py`: молчит пока нет работы, печатает и завершается → будит Клода, ноль токенов в простое)
- [x] Deprecated-скиллы удалены (`move_card`, `update_card_description`) — валидацию воркфлоу больше нельзя обойти
- [x] Новый скилл `workflow_state` — полный снимок контекста одной командой
- [x] `.claude/trello.json` добавлен в `.gitignore` (credentials не попадут в git)
- [x] **Абстракция BoardBackend** (`backend.py`) — весь workflow-код говорит с нейтральным интерфейсом доски (колонки/карточки/комментарии/чеклисты); Trello — просто первая реализация. Миграция на свой веб-интерфейс = написать `WebBackend`, зарегистрировать в `_BACKENDS`, поставить `"backend": "web"` в конфиге. Больше ничего не меняется.

---

## 📁 Структура проекта

```
ShayaBrusilovskySkills/
├── src/mcp_dev_skills/
│   ├── server.py                    # MCP-сервер
│   ├── monitor.py                   # Фоновый монитор «жди работу» (не MCP-инструмент)
│   ├── loader.py                    # Динамическая загрузка скиллов
│   ├── config.py                    # Чтение .skills.json
│   ├── security.py                  # Песочница путей
│   └── skills/development/
│       ├── common/
│       │   ├── project_analyzer.py
│       │   ├── file_operations.py
│       │   ├── setup_skills.py
│       │   ├── development_methodology.py
│       │   └── workflow_state.py    # НОВЫЙ: снимок контекста
│       ├── trello/
│       │   ├── trello.py            # ЕДИНЫЙ скилл доски (10 действий, не привязан к Trello)
│       │   ├── backend.py           # Интерфейс BoardBackend + TrelloBackend + get_backend()
│       │   ├── errors.py            # Нейтральный BoardAPIError (скиллы ловят только его)
│       │   ├── trello_api.py        # HTTP-клиент Trello (используется только TrelloBackend)
│       │   ├── config_utils.py      # Scope-aware конфиг
│       │   └── WORKFLOW.md
│       ├── branching/
│       │   └── branching_simple.py  # Стратегия: простой workflow (через trello_api)
│       └── local_dev/
│           └── local_dev_default.py # Стратегия: правила локальной разработки
├── .skills.json
├── SKILLS_GUIDE.md
└── PROJECT_STATUS.md
```

---

## 📋 Инвентарь скиллов

### ГРУППА: development.common (5 скиллов)

#### **1. project_analyzer**
- Трёхуровневый анализ workspace: обзор → детали части → точные пути файлов (+ уровень 0: дерево)
- Определяет язык/фреймворк, делит проект на логические части

#### **2. file_operations**
- Безопасное чтение файлов workspace (песочница путей)

#### **3. setup_skills**
- Список доступных скиллов, генерация `.skills.json`

#### **4. development_methodology**
- Универсальная трёхстадийная система: Проектирование → Развертывание → Тестирование
- **Стадии:** Проектирование [x], Развертывание [x], Тестирование [ ]

#### **5. workflow_state** *(новый)*
- Снимок для начала сессии: текущий scope/доска Trello, карточки в рабочих колонках (с id), git-ветка, незакоммиченные файлы, последние коммиты
- Работает и без настроенного Trello (покажет только git)

---

### ГРУППА: development.trello (1 скилл, 10 действий)

#### **trello** — все операции Trello через параметр `action`

| Действие | Что делает |
|---|---|
| `configure` | Проверка credentials, создание недостающих колонок, сохранение scope-конфига |
| `switch_scope` | Список досок / переключение scope / регистрация планируемых scope |
| `check_board` | **Одноразовая** проверка работы в Inbox/Approved (без цикла — цикл на стороне клиента) |
| `get_card` | Полные детали карточки: описание, метки, чеклисты (с id), комментарии |
| `set_plan` | План в описание; автобэкап исходной задачи в комментарий; определение языка |
| `ask_questions` | Чеклисты Questions/Answers с фильтром по tech_level; карточка → Planning |
| `change_status` | Перемещение карточки **с валидацией воркфлоу** (правила ниже) |
| `add_comment` | Комментарий (автопрефикс 🤖) |
| `create_checklist` | Пустой чеклист на карточке |
| `add_checklist_item` | Пункт в чеклист |

**Правила воркфлоу (зашиты в код, обходных путей нет):**
- Claude может: `Inbox→Planning`, `Approved→In Progress`, `In Progress→Review`
- Только пользователь: `Planning→Approved`, `Review→Done`

**Конфиг** (`.claude/trello.json`, в gitignore):
```json
{
  "api_key": "...",
  "token": "...",
  "current_scope": "rental",
  "known_scopes": ["crm", "rental"],
  "boards": {
    "rental": {
      "board_id": "...",
      "board_url": "...",
      "board_name": "...",
      "tech_level": 0,
      "language": "auto"
    }
  }
}
```

---

### ГРУППА: development.branching (1 скилл)

#### **branching_simple**
- `action="assign"`: создать git-ветку для карточки, комментарий в Trello, карточка → In Progress
- `action="update_status"`: синхронизировать коммиты в комментарий Trello
- `action="list"`: активные ветки с числом коммитов
- Использует общий клиент `trello_api`

---

### ГРУППА: development.local_dev (1 скилл)

#### **local_dev_default**
- Свод правил (только инструкции): локальное окружение, тестовые данные, dev-конфиг, помощники воркфлоу

---

## 🔧 Использование

### Конфигурация (.skills.json)
```json
{
  "enabled_paths": [
    "development.common",
    "development.trello",
    "development.branching",
    "development.local_dev"
  ],
  "disabled_skills": []
}
```

### Паттерн мониторинга
- По запросу: `trello(action='check_board')` — мгновенный ответ.
- Постоянно: `python -m mcp_dev_skills.monitor --workspace <path> --interval 30` запускается как **фоновый процесс**. Пока работы нет — молчит (Клод не просыпается → ноль токенов); когда работа появилась — печатает список карточек и завершается, это будит Клода. Никогда — цикл внутри MCP-инструмента.

---

## 🚀 Следующие шаги

- [ ] Наполнить `local_dev_default` конкретными примерами тестовых данных
- [ ] Альтернативные локальные стратегии (`local_dev_strict` и др.)
- [ ] Группа CI/CD для деплой-скиллов
- [ ] Группа CLI-скаффолдинга для быстрого старта проектов
- [ ] project_analyzer: не заходить в .venv/node_modules при детекции фреймворка (известная проблема)
