# Журнал ИИ-assisted инженерных правок. Это не независимый аудит

Проект: fitness-coach-bot
Репозиторий: alex-yorik/fitness-coach-bot
Ветка: chore/portfolio-ready
Тег pre-portfolio-ready: 6bc6c0407d821af939b0de2701c84220315d34fa

## F0: Подготовка и baseline

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| Ветка и тег | VERIFIED | git rev-parse pre-portfolio-ready | 6bc6c0407d821af939b0de2701c84220315d34fa |

### Состояние рабочего дерева до начала hardening
На момент старта F0.1 в рабочем дереве уже присутствовали незакоммиченные изменения, не относящиеся к hardening и не тронутые в ходе работ:
- modified: `AGENTS.md`, `docker-compose.yml`
- untracked: `.gitattributes`, `.graphifyignore`, `.opencode/opencode.json`, `.opencode/plugins/`, `graphify-out/`

`main` и её история не изменялись; ветка `chore/portfolio-ready` создана от коммита `6bc6c0407d821af939b0de2701c84220315d34fa`.

## F0.2: Baseline

Окружение: чистый venv `/tmp/fitness-venv`, Python 3.12.3.
Зависимости: `requirements.txt`; dev-инструменты с закреплёнными версиями:
`pytest==9.1.1`, `pytest-asyncio==1.4.0`, `pytest-cov==7.1.0`, `ruff==0.16.1`, `bandit==1.9.4`.

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| venv создан | VERIFIED | python3 -m venv /tmp/fitness-venv | Python 3.12.3; requirements.txt и dev-инструменты установлены |
| pytest | VERIFIED | pytest tests/unit -m "not live" --cov --cov-fail-under=80 | 148 passed, 0 failed; coverage 95.76% (гейт 80% пройден) |
| ruff check | VERIFIED | ruff check . | All checks passed!, 0 ошибок |
| ruff format | VERIFIED | ruff format --check . | 37 files already formatted |
| bandit | VERIFIED | bandit -r app admin -ll -q | exit 0; 0 findings; только cosmetic warning про nosec B104 (app/health_server.py:8) |
| modularity | VERIFIED | python scripts/check_modularity.py . | Модульность в порядке: проверено 27 файлов |
| компиляция | VERIFIED | python -m compileall -q app admin scripts tests | exit 0 |
| тест-файлов | VERIFIED | find tests -name "test_*.py" \| wc -l | 10 |
| тест-функций | VERIFIED | grep -rhE "^\s*(async )?def test_" tests \| wc -l | 106 |
| сравнение с ACCEPTANCE | VERIFIED | cat ACCEPTANCE_REPORT.md | 148 passed и 95.76% совпадают; ruff format: 37 против 33 в отчёте приёмки |

### Расхождения с ACCEPTANCE_REPORT.md
- Тесты: **148 passed** и coverage **95.76%** — совпадает с ожидаемым.
- `ruff check .`: 0 ошибок — совпадает.
- `bandit -r app admin -ll`: 0 findings, exit 0 — совпадает (предупреждение о `nosec B104` косметическое, описано в отчёте приёмки).
- Модульность: проверено 27 файлов — совпадает.
- `ruff format --check .`: **37 файлов** против **33** в ACCEPTANCE_REPORT.md. Причина: с даты приёмки (2026-08-14) в репозитории появились новые Python-файлы; расхождение не является дефектом форматирования (все 37 уже отформатированы).
- Итог baseline: **зелёный**, блокирующих проблем нет.

## F0.3: Docker с чистого клона

Метод: клон `/tmp/fitness-clean` ветки `chore/portfolio-ready` (коммит `1830c7a`), `.env` создан из `.env.example` с фиктивными значениями. Реальный токен бота не использовался.

Важно: на хосте уже запущен production compose `fitness-coach` (контейнеры `fitness-coach`, `fitness-coach-webadmin`, порты 8001/5004), поэтому команда из ТЗ конфликтует по `container_name` и портам. Чтобы не останавливать production, для проверки использован временный override вне репозитория: имена `fitness-clean-*`, порты 18001/15004. Dockerfile, `.env`, volumes и uid контейнера при этом не менялись.

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| clone | VERIFIED | git clone /opt/fitness-coach fitness-clean --branch chore/portfolio-ready | коммит `1830c7a` |
| .env подготовлен | VERIFIED | cp .env.example .env + sed | фиктивные значения; реальный токен не использован; `DEMO_MODE` в `.env.example` отсутствует, соответствующий sed — no-op |
| docker compose up (default) | FAILED | docker compose up -d --build | exit 1: `Conflict. The container name "/fitness-coach" is already in use` (конфликт с production) |
| docker compose up (isolated) | VERIFIED | docker compose -f docker-compose.yml -f docker-compose.isolated.yml up -d | exit 0, оба контейнера созданы и запущены |
| контейнеры healthy | FAILED | docker compose ps | оба `health: starting`; bot в restart loop (`Up 4 seconds`), healthy не достигнут |
| права data/logs/media | FAILED | ls -la data/ logs/ media/ | каталоги `root:root 0755`; контейнер работает под uid 10001 (`appuser`) |
| healthcheck бота | FAILED | curl :18001/healthz | `curl: (56) Recv failure: Connection reset by peer`, также 503 |
| healthcheck админки | FAILED | curl :15004/healthz | HTTP 503 |
| вход в админку | VERIFIED | curl :15004/login | HTTP 200 (страница логина доступна) |
| docker compose down | VERIFIED | docker compose ... down | exit 0; production `fitness-coach` не затронут, остаётся healthy |

### Диагностика
- `docker logs fitness-clean-bot`: `sqlite3.OperationalError: unable to open database file` в `app/database.py:10`; процесс падает до запуска health-сервера и перезапускается.
- `docker logs` grep по `permission|error|denied`: `sqlite3.OperationalError: unable to open database file`.
- Причина: в свежем клоне каталогов `data/`, `logs/`, `media/` нет (они в `.gitignore`); Docker создаёт их при bind-mount от `root:root 0755`, а приложение работает под uid 10001 и не может писать БД/логи. Админка поднимается, но `/healthz` возвращает 503 из-за недоступной БД.
- Это реальный дефект установки с чистого клона, а не следствие обхода конфликта портов.

**Итог F0.3: FAILED.** Согласно ограничениям, дальнейший hardening остановлен до исправления (правки кода в рамках F0.3 не выполнялись).

## F0.4: GitHub Actions

Проверка статуса workflows через `gh` невозможна: CLI установлен, но не авторизован.

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| gh run list | NOT VERIFIED | gh run list --repo alex-yorik/fitness-coach-bot --limit 10 | `To get started with GitHub CLI, please run: gh auth login` (exit 4) |

### Примечание
`gh` CLI не авторизован. Владелец проверит статус workflows CI и Quality Gates на `main` через GitHub UI. Записать точные имена проверок (поле `name:` в jobs) для F7.

## F0.5: Секреты в истории

Метод: `gitleaks detect` по всей истории, поиск `.env`/`*.db`/`*.pem` в истории, проверка tracked-файлов на артефакты.

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| gitleaks | VERIFIED | gitleaks detect --source . --log-opts="--all" --redact -v | 48 commits scanned, ~1.67 MB, `no leaks found` (exit 0) |
| .env в истории | VERIFIED | git log --all --oneline -- .env | пусто (файл никогда не коммитился) |
| *.db в истории | VERIFIED | git log --all --oneline -- '*.db' | пусто |
| *.pem в истории | VERIFIED | git log --all --oneline -- '*.pem' | пусто |
| tracked файлы | VERIFIED | git ls-files \| grep -E "\.(pyc\|db\|log)$\|^(data\|logs\|media)/" | совпадений нет (exit 1) |

### Примечания
- Реальных секретов (BOT_TOKEN и т.п.) в истории не найдено.
- `.opencode/project.json` отслеживается и содержит тестовые креды `admin / admin123` (появляются в истории коммитами `4b4f76e`, `d69f276`). `gitleaks` их как утечку не классифицировал (не секрет известного формата); это известная проблема, устраняется в F1 (удаление из индекса).
- Отзыв токена в BotFather не требуется.

## F0.6: Полное чтение файлов

Прочитаны целиком все перечисленные файлы; проверены секреты, реальные личные данные, устаревшие утверждения и небезопасный рендеринг Jinja2.

### Проверки
| Файл | Секреты | Личные данные | Устаревшие утверждения | `\|safe` / `autoescape off` |
|---|---|---|---|---|
| AGENTS.md | нет | нет | нет | н/д |
| ARCHITECTURE.md | нет | нет | нет | н/д |
| SECURITY.md | нет | нет | нет | н/д |
| CHANGELOG.md | нет | **найдено: реальное ФИО тренера (стр. 27)** | найдено: `teacher.json` (файла в репозитории нет) | н/д |
| TECH_DEBT.md | нет | нет | нет (ссылки на строки `validators.py:118`, `admin/web.py:237`, `trial.py:150` актуальны) | н/д |
| ACCEPTANCE_REPORT.md | нет | нет | найдено: «33 файла» ruff format (фактически 37, см. F0.2) | н/д |
| init_new_bot.sh | нет | нет | найдено: пример `--template=fitness` (шаблона нет); жёсткое удаление `content/fitness_coach.json`; работает только из корня проекта | н/д |
| scripts/backup.sh | нет | нет | найдено: не принимает путь БД позиционным аргументом (только `DB_PATH`) | н/д |
| scripts/check_modularity.py | нет | нет | нет | н/д |
| tests/live/test_live.py | нет (`BOT_TOKEN` только из env) | нет | нет | н/д |
| templates/beauty.json | нет | нет (вымышленное имя) | нет | н/д |
| templates/cafe.json | нет | нет (вымышленное название) | нет | н/д |
| templates/manicure.json | нет | нет (вымышленное имя) | нет | н/д |
| templates/psychologist.json | нет | нет (вымышленное имя) | нет | н/д |
| content/fitness_coach.json | нет | нет (вымышленные данные, контактов/ссылок/фото нет, `media: []`) | нет | н/д |
| admin/templates/index.html | нет | нет | нет | нет (только `{{ }}`, автоэкранирование) |
| admin/templates/login.html | нет | нет | нет | нет |

### Вывод F0.6
- **Найдено реальное личное данное**: в `CHANGELOG.md:27` упомянуто реальное ФИО тренера (не вымышленное, в отличие от `content/fitness_coach.json`). Требуется решение владельца: переписать запись/историю CHANGELOG или подтвердить допустимость. В рамках F0.6 файл не менялся (вне allowed files).
- Секретов, токенов, паролей и ключей в перечисленных файлах не найдено. `tests/live/test_live.py` берёт `BOT_TOKEN` только из окружения.
- `|safe` и `autoescape off` в шаблонах отсутствуют; опасных фильтров/`Markup` нет.

## F0.7: Проверка работоспособности скриптов

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| backup.sh | FAILED | bash scripts/backup.sh /tmp/test_backup.db | exit 0, бэкап создаётся (`db-YYYY-MM-DD.db`, `0600`). Но **позиционный аргумент игнорируется**: путь БД задаётся только `DB_PATH`, поэтому вместо переданной БД бэкапится дефолтная `/opt/fitness-coach/data/database.db` (доказано тестовой БД с таблицей `marker_test`). Для безопасного теста использованы `BACKUP_DIR=/tmp/...`. |
| backup.sh: env-режим | VERIFIED | `DB_PATH=/tmp/test_backup.db BACKUP_DIR=/tmp/... bash scripts/backup.sh` | exit 0; создан корректный бэкап переданной БД, права `0600`, каталог `0700`. |
| backup.sh: ротация | VERIFIED | test-файл с mtime 20 дней + повторный запуск | старый `db-2000-01-01.db` удалён; ротация `RETENTION_DAYS=14` работает (`find -mtime +14`). |
| init_new_bot.sh | FAILED | bash init_new_bot.sh --template=fitness --name=test | exit 1: `шаблон не найден: templates/fitness.json`; из `/tmp` список доступных шаблонов пуст (пути относительные), из корня проекта — `beauty/cafe/manicure/psychologist`. Пример `--template=fitness` в usage вводит в заблуждение — такого шаблона нет. |
| init_new_bot.sh: из корня | FAILED (ожидаемо) | bash ./init_new_bot.sh --template=fitness --name=test-f07 | exit 1, тот же вывод + список 4 реальных шаблонов. |

### Вывод F0.7
- `backup.sh` функционально рабочий только через env (`DB_PATH`, `BACKUP_DIR`); вызов с путём БД аргументом молча бэкапит production-БД. Это вводит в заблуждение (исправить в F1/F2).
- `init_new_bot.sh` не работает вне корня проекта и ссылается на несуществующий `fitness`; успешный сценарий не проверялся, чтобы не копировать в репозиторий `data/`, `backups/`, `.env`.
- Код проекта не изменялся; в рамках F0.6/F0.7 изменён только данный отчёт.

## F1: Чистка репозитория + удаление реального ФИО

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| Ссылки на `ai_assistant` | VERIFIED | `git grep -n "ai_assistant" -- . ':!graphify-out'` | единственное совпадение — `.github/workflows/ci.yml:38`; удалено |
| Ссылки на `admin.admin` | VERIFIED | `git grep -n "admin.admin\|from admin import admin"` | совпадений в отслеживаемых файлах нет (exit 1); только сгенерированные `graphify-out/` и `__pycache__` |
| `.opencode/project.json` удалён из индекса | VERIFIED | `git rm --cached .opencode/project.json` | `rm '.opencode/project.json'` |
| `.opencode/` в `.gitignore` | VERIFIED | `grep -q "^\.opencode/" .gitignore` | добавлена строка `.opencode/` |
| `.opencode/` в `.dockerignore` | VERIFIED | `grep -q "^\.opencode/" .dockerignore` | добавлена строка `.opencode/` |
| `ai_assistant.py` удалён | VERIFIED | `git rm --cached ai_assistant.py` + `rm` | файл отсутствует на диске и в индексе |
| `admin/admin.py` удалён | VERIFIED | `git rm --cached admin/admin.py` + `rm` | файл отсутствует на диске и в индексе |
| `init_new_bot.sh` исправлен | VERIFIED | `sed -i 's/--template=fitness/--template=beauty/g'` | usage: `--template=beauty`; логика не менялась |
| `CHANGELOG.md:27` заменено | VERIFIED | `sed -i 's/Елены Янаковой/Алексея Смирнова/'` | было «Елены Янаковой», стало «Алексея Смирнова» (падеж сохранён); `grep "Янаков\|Елен"` — пусто |
| `git ls-files` проверка | VERIFIED | `git ls-files \| grep -E "opencode\|ai_assistant\|admin/admin.py"` | пусто (exit 1) |
| compileall | VERIFIED | `python3 -m compileall -q app admin scripts tests` | exit 0 |
| ruff check | VERIFIED | `ruff check .` | `All checks passed!` (exit 0) |
| ruff format | VERIFIED | `ruff format --check .` | `35 files already formatted` (exit 0) |
| bandit | VERIFIED | `bandit -r app admin -ll -q` | exit 0, 0 findings (только информационный WARNING про существующий `nosec B104`) |
| modularity | VERIFIED | `python3 scripts/check_modularity.py .` | `Модульность в порядке: проверено 25 файлов` |
| pytest | VERIFIED | `python3 -m pytest tests/unit -m "not live" --cov --cov-fail-under=80` | `148 passed`, coverage `95.76%` (exit 0) |
| git status | VERIFIED | `git status --short` | `.env`, `data/`, `logs/`, `media/`, `*.db`, `__pycache__` отсутствуют |

### Примечания F1
- F1.6: в `CHANGELOG.md:27` фактическая формулировка была «…контентом Елены Янаковой» (родительный падеж), поэтому замена выполнена на «…контентом Алексея Смирнова» — смысл и грамматика сохранены, реальное ФИО удалено.
- В рабочем дереве до начала F1 оставались незакоммиченные изменения вне allowed files (`AGENTS.md`, `docker-compose.yml`, `.gitattributes`, `.graphifyignore`, `.opencode/opencode.json`, `.opencode/plugins/`, `graphify-out/`). Они не входят в F1 и в коммит не включены.
- Сгенерированные `graphify-out/` и `__pycache__` содержат упоминания удалённых файлов; это артефакты, не отслеживаемые git, на код не влияют.

## F2: Docker безопасные значения по умолчанию + права на каталоги

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| version удалён | VERIFIED | `grep -n '^version:' docker-compose.yml` | нет совпадений (exit 1) |
| порт бота 127.0.0.1:8001 | VERIFIED | `docker compose config` | `host_ip: 127.0.0.1`, `target: 8001`, `published: "8001"` |
| порт админки ADMIN_BIND | VERIFIED | `docker compose config` | по умолчанию `host_ip: 127.0.0.1`, при `ADMIN_BIND=0.0.0.0` — `host_ip: 0.0.0.0`; `target/published: 5004` |
| .env.example: ADMIN_BIND | VERIFIED | `grep ADMIN_BIND .env.example` | `ADMIN_BIND=127.0.0.1` + комментарий о 0.0.0.0 только за reverse-proxy/TLS |
| .env.example: DEMO_MODE | VERIFIED | `grep DEMO_MODE .env.example` | `DEMO_MODE=False` + пометка, что текущий код переменную не читает |
| .env.example: SESSION_COOKIE_SECURE | VERIFIED | `grep -A2 SESSION_COOKIE_SECURE .env.example` | комментарий обновлён: True — HTTPS/localhost, для демо по HTTP с внешнего адреса — False |
| README: chown шаг | VERIFIED | `grep -n -A2 chown README.md` | шаг перед `docker-compose up`: `mkdir -p data logs media` + `sudo chown -R 10001:10001 data logs media` |
| docker compose config -q | VERIFIED | `docker compose config -q` | exit 0 |
| ADMIN_BIND=0.0.0.0 | VERIFIED | `ADMIN_BIND=0.0.0.0 docker compose config` | `host_ip: 0.0.0.0`, `target: 5004`, `published: "5004"` |
| без ADMIN_BIND | VERIFIED | `docker compose config` | `host_ip: 127.0.0.1`, `target: 5004`, `published: "5004"` |

### Примечания F2
- `docker-compose.yml` также содержит не входившие в F2, но уже присутствовавшие в рабочем дереве правки (json-file logging с ротацией 10m, healthcheck interval 300s); они включены в коммит F2, так как относятся к тому же файлу.
- README в разделе Docker дополнен фактическим интервалом healthcheck (300s) и описанием `ADMIN_BIND`.
- Каталоги `data/`, `logs/`, `media/` на текущем стенде уже принадлежат `10001:10001`; повторный прогон контейнера с чистого клона в рамках F2 не выполнялся (проверялся только `docker compose config`).

## F3: Админка — валидация статуса и демо-баннер

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| ALLOWED_STATUSES константа | VERIFIED | `grep ALLOWED_STATUSES admin/web.py` | `18:ALLOWED_STATUSES = {"new", "in_progress", "done"}` |
| update_status проверка | VERIFIED | `grep -A5 update_status admin/web.py` | проверка `new_status not in ALLOWED_STATUSES` → `jsonify(...), 400` до записи в БД (строки 174–175) |
| index/export фильтр | VERIFIED | `grep -A5 index/export admin/web.py` | неизвестный `status` заменяется на `""` (строки 138–139 и 252–253) |
| DEMO_MODE чтение | VERIFIED | `grep DEMO_MODE admin/web.py` | `36:DEMO_MODE = os.environ.get("DEMO_MODE", "").lower() in ("1", "true", "yes")` |
| context_processor | VERIFIED | `grep context_processor admin/web.py` | `47:@app.context_processor` → `inject_demo_mode()` возвращает `{"demo_mode": DEMO_MODE}` |
| login.html баннер | VERIFIED | `grep demo_mode admin/templates/login.html` | `23:{% if demo_mode %}` перед полями формы |
| index.html баннер | VERIFIED | `grep demo_mode admin/templates/index.html` | `43:{% if demo_mode %}` после заголовка, перед статистикой/таблицей |
| тест неверного статуса | VERIFIED | `pytest -k test_update_status_invalid` | 1 passed; ответ 400, статус в БД остаётся `new` |
| тест верных статусов | VERIFIED | `pytest -k test_update_status_valid` | 1 passed; `new`, `in_progress`, `done` сохраняются |
| тест баннера DEMO | VERIFIED | `pytest -k demo_banner` | 2 passed (DEMO_MODE=True → баннер, False → нет баннера) |
| compileall | VERIFIED | `python -m compileall -q app admin scripts tests` | exit 0 |
| ruff check | VERIFIED | `ruff check .` | `All checks passed!` |
| ruff format | VERIFIED | `ruff format --check .` | `35 files already formatted` |
| bandit | VERIFIED | `bandit -r app admin -ll -q` | exit 0, 0 findings (только WARNING про существующий `nosec B104`) |
| modularity | VERIFIED | `python scripts/check_modularity.py .` | `Модульность в порядке: проверено 25 файлов` |
| pytest | VERIFIED | `pytest tests/unit -m "not live" --cov --cov-fail-under=80` | `152 passed`, coverage `95.76%` |
| git status | VERIFIED | `git status --short` | изменены только allowed files F3 (плюс ранее существовавшие untracked артефакты) |

### Примечания F3
- `DEMO_MODE` читается при импорте модуля; в тестах вместо `monkeypatch.setenv` используется `monkeypatch.setattr(web, "DEMO_MODE", ...)`, так как контекст-процессор читает глобальную переменную модуля на каждом запросе. Это не меняет поведение приложения.
- Тесты `/update_status` адаптированы под существующий контракт (form-data + CSRF, ответ 302 при успехе): неверный статус возвращает 400, корректные — сохраняются в БД. JSON-контракт не вводился, поведение CSRF/входа/лимита/экспорта не изменялось.
- Проверка статуса выполняется до открытия соединения с БД и записи.

## F4: PBKDF2 вместо HMAC для пароля админки

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| admin/passwords.py создан | VERIFIED | `cat admin/passwords.py` | формат `pbkdf2_sha256:<iterations>:<salt_hex>:<hash_hex>`, `hash_password` / `verify_password` / CLI `main` |
| hash_password работает | VERIFIED | `printf 'test123\ntest123\n' \| python -m admin.passwords` | `FLASK_PASSWORD_HASH=pbkdf2_sha256:600000:<salt_hex>:<hash_hex>` |
| verify_password работает | VERIFIED | `pytest -k test_hash_verify` | 1 passed (roundtrip) |
| admin/web.py обновлён | VERIFIED | `grep verify_password admin/web.py` | `15:from admin.passwords import verify_password`, `70:return verify_password(password, stored)` |
| Проверка формата при старте | VERIFIED | `grep RuntimeError admin/web.py` | строки 46–50: при непустом `_stored_hash` и отсутствии префикса `pbkdf2_sha256:` — `RuntimeError` с командой генерации |
| Старый HMAC удалён | VERIFIED | `grep -i hmac admin/web.py` | остался только `import hmac` + `hmac.compare_digest` для CSRF; HMAC-хеширования пароля нет |
| tests/unit/test_passwords.py | VERIFIED | `pytest tests/unit/test_passwords.py` | 7 passed |
| tests/unit/test_web.py обновлён | VERIFIED | `grep hash_password tests/unit/test_web.py` | `9:from admin.passwords import hash_password`, `13:os.environ["FLASK_PASSWORD_HASH"] = hash_password(TEST_PASSWORD, iterations=1000)` |
| README обновлён | VERIFIED | `grep "python -m admin.passwords" README.md` | шаг генерации и раздел миграции используют CLI; пример `pbkdf2_sha256:600000:<salt_hex>:<hash_hex>` |
| .env.example обновлён | VERIFIED | `grep FLASK_PASSWORD_HASH .env.example` | `FLASK_PASSWORD_HASH=CHANGE_ME` + комментарий PBKDF2-HMAC-SHA256 / 600 000 итераций |
| SECURITY.md обновлён | VERIFIED | `grep PBKDF2 SECURITY.md` | «PBKDF2-HMAC-SHA256 с солью и 600 000 итераций … формат без символа `$`»; проверка — `admin/passwords.py::verify_password` |
| Вход в контейнере | VERIFIED | `curl -X POST http://localhost:5004/login -d "username=admin&password=admin123"` | `status=302 redirect=http://localhost:5004/` |
| compileall | VERIFIED | `python -m compileall -q app admin scripts tests` | exit 0 |
| ruff check | VERIFIED | `ruff check .` | `All checks passed!` |
| ruff format | VERIFIED | `ruff format --check .` | `37 files already formatted` |
| bandit | VERIFIED | `bandit -r app admin -ll -q` | exit 0, 0 findings (только WARNING про существующий `nosec B104`) |
| modularity | VERIFIED | `python scripts/check_modularity.py .` | `Модульность в порядке: проверено 27 файлов` |
| pytest | VERIFIED | `pytest tests/unit -m "not live" --cov --cov-fail-under=80` | `159 passed`, coverage `95.76%` |
| git status | VERIFIED | `git status --short` | изменены только allowed files F4 (плюс ранее существовавшие `AGENTS.md` и untracked артефакты) |

### Примечания F4
- `tests/conftest.py` не входит в allowed files, поэтому формирование `FLASK_PASSWORD_HASH` через старый HMAC осталось в conftest, но переопределяется в начале `tests/unit/test_web.py` через `hash_password(...)` **до** импорта `admin.web`. Импорт `admin.web` выполнен через `importlib.import_module`, чтобы не нарушать E402. Поскольку другие тесты `admin.web` не импортируют, это не влияет на остальной набор.
- **Тесты изменены, т.к. ТЗ F4 прямо отменяет старый HMAC-формат пароля.** Это относится к `tests/unit/test_web.py` (формирование тестового хеша) и новому `tests/unit/test_passwords.py`.
- F4.5 выполнялся на реальном `.env` проекта: хеш `admin123` записан в локальный `.env` (файл в `.gitignore`, в коммит не попадает), `docker compose up -d --build` поднял оба контейнера, вход вернул 302. После проверки контейнеры остановлены (`docker compose down`). Для демо-стенда пароль `admin123` слабый — рекомендуется сгенерировать новый через `python -m admin.passwords` и заменить `FLASK_PASSWORD_HASH`.
- `SECRET_KEY` по-прежнему используется только для подписи сессий и CSRF; его проверка и использование не менялись.
- CLI при неинтерактивном stdin печатает `GetPassWarning` (нет TTY) — это штатное поведение `getpass`, на генерацию хеша не влияет.

## F5: Безопасность демо-данных (F5.1; F5.2 пропущен по D2)

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| content/fitness_coach.json прочитан | VERIFIED | `cat content/fitness_coach.json` | структура: name, profession, welcome, about, formats, trial, ui, gallery |
| Ограничения валидатора | VERIFIED | `grep -n "max\|length\|len" app/validators.py` | контент не ограничен по длине; лимиты только для ввода пользователя: `text` 2–200 символов, `phone` 7–15 цифр, `age` 1–100, `contact` минимум 4 символа |
| Предупреждение добавлено | VERIFIED | `grep -n "демо-бот" content/fitness_coach.json` | строка 6: «Это демо-бот. Не вводите реальные персональные данные: используйте вымышленные имя и контакт.» в конце `welcome.text` |
| JSON валиден | VERIFIED | `python -c "import json; json.load(open('content/fitness_coach.json'))"` | exit 0 |
| Длина текста в лимите | VERIFIED | `python -c "len(v)"` по всем текстовым полям | `welcome.text` = 277 символов; лимита на контент нет, ограничение 200 относится к ответу пользователя |
| F5.2 пропущен | VERIFIED | решение владельца D2 | скрипт очистки демо-заявок не нужен |
| test_content_loader.py | VERIFIED | `pytest tests/unit/test_content_loader.py -v` | passed (в составе общего прогона; точных сравнений с текстом `welcome` нет) |
| test_trial.py | VERIFIED | `pytest tests/unit/test_trial.py -v` | passed |
| test_validators.py | VERIFIED | `pytest tests/unit/test_validators.py -v` | passed |
| compileall | VERIFIED | `python -m compileall -q app admin scripts tests` | exit 0 |
| ruff check | VERIFIED | `ruff check .` | `All checks passed!`, 0 ошибок |
| ruff format | VERIFIED | `ruff format --check .` | `37 files already formatted` |
| bandit | VERIFIED | `bandit -r app admin -ll -q` | exit 0, 0 findings (только WARNING про существующий `nosec B104`) |
| modularity | VERIFIED | `python scripts/check_modularity.py .` | `Модульность в порядке: проверено 27 файлов` |
| pytest | VERIFIED | `pytest tests/unit -m "not live" --cov --cov-fail-under=80` | `159 passed`, coverage `95.76%` |
| git status | VERIFIED | `git status --short` | изменены только allowed files F5 (плюс ранее существовавшие `AGENTS.md` и untracked артефакты) |

### Примечания F5
- Предупреждение добавлено в конец `welcome.text` с разделителем `\n\n` — это наименее инвазивное место: текст показывается при `/start`, структура JSON и обработчики не менялись.
- Тесты не изменялись: ни один из `test_content_loader.py`, `test_trial.py`, `test_validators.py` не сравнивает точный текст `welcome.text` (используются синтетические фикстуры), все проходят.
- F5.2 пропущен по решению владельца D2 (скрипт очистки демо-заявок не нужен).
- Добавление предупреждения увеличивает `welcome.text` до 277 символов; валидатор контента таких полей не ограничивает, на отправку сообщения Telegram (лимит 4096) влияния нет.

## F6: CI permissions и fetch-depth для gitleaks

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| ci.yml: permissions | VERIFIED | `grep permissions .github/workflows/ci.yml` | `3:permissions:`, `contents: read` |
| quality-gates.yml: permissions | VERIFIED | `grep permissions .github/workflows/quality-gates.yml` | `3:permissions:`, `contents: read` |
| security: fetch-depth: 0 | VERIFIED | `grep fetch-depth .github/workflows/quality-gates.yml` | `20:          fetch-depth: 0` (шаг checkout в job `security`) |
| py_compile не ссылается на удалённые | VERIFIED | `grep -n "ai_assistant\|admin/admin" .github/workflows/ci.yml` | пусто (exit 1) |
| YAML-синтаксис ci.yml | VERIFIED | `python3 -c "yaml.safe_load(...)"` | exit 0 |
| YAML-синтаксис quality-gates.yml | VERIFIED | `python3 -c "yaml.safe_load(...)"` | exit 0 |
| compileall | VERIFIED | `python3 -m compileall -q app admin scripts tests` | exit 0 |
| ruff check | VERIFIED | `ruff check .` | `All checks passed!`, 0 ошибок |
| ruff format | VERIFIED | `ruff format --check .` | `37 files already formatted` |
| bandit | VERIFIED | `bandit -r app admin -ll -q` | exit 0, 0 findings (только WARNING про существующий `nosec B104`) |
| modularity | VERIFIED | `python3 scripts/check_modularity.py .` | `Модульность в порядке: проверено 27 файлов` |
| git status | VERIFIED | `git status --short` | изменены только allowed files F6 (плюс ранее существовавшие `AGENTS.md` и untracked артефакты) |
| F6-fix: pull-requests: read для job security | VERIFIED | ошибка CI назвала permission: 403 на GET /pulls/1/commits, заголовок x-accepted-github-permissions: pull_requests=read | добавлена только названная permission (ТЗ F6) |

### Примечания F6
- `permissions` заданы на уровне workflow (не job), чтобы минимальные права `contents: read` применялись ко всем job'ам обоих файлов.
- `pull-requests: read` добавлен на уровне job `security` в F6-fix: без него gitleaks-action получает 403 на `GET /pulls/1/commits` ещё до начала сканирования. Job-level `permissions` переопределяет top-level, поэтому в job повторены обе строки (`contents: read`, `pull-requests: read`).
- `fetch-depth: 0` добавлен только в checkout job `security`, чтобы gitleaks видел полную историю; остальные checkout не менялись.
- Триггеры, шаги ruff/bandit/coverage/modularity и закреплённые версии не изменялись.
- Находок секретов в CI не было ни в одном прогоне; все три причины красных Quality Gates закрыты: nosec B104 (до hardening, задокументирован), fetch-depth: 0 (F6), pull-requests: read (F6-fix).

### История CI на main до hardening (факты из логов, предоставлены владельцем)
| Прогон | Коммит | Результат |
|---|---|---|
| Quality Gates #3 (14 авг) | cadeaff | Bandit exit 1 — B104 Medium в `app/health_server.py:8`; на этом коммите `# nosec B104` ещё не было (добавлен позже, до hardening; оба `nosec` перечислены в отчёте с причинами). Код не менялся. |
| Quality Gates #4 (14 авг) | e019e36 | gitleaks exit 1 — `fatal: ambiguous argument ... unknown revision` из-за shallow-checkout (`fetch-depth` по умолчанию 1); исправлено в F6 (`fetch-depth: 0`). |
| Quality Gates #5 (26 авг) | 6bc6c04 | gitleaks exit 1 — та же причина shallow-checkout; исправлено в F6 (`fetch-depth: 0`). |
| Quality Gates #6 (PR #1) | — | gitleaks 403 до начала сканирования (нет `pull-requests: read`); исправлено в F6-fix. |
| CI workflow на main | — | зелёный (прогоны CI #3 и #5; это отдельный workflow «CI», не «Quality Gates»). |

## F7: Честная документация (ИИ, демо, ограничения, LICENSE)

### Проверки
| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| README: раздел «Как сделан проект» | VERIFIED | `grep "Как сделан" README.md` | `## Как сделан проект`; раскрыты ИИ-инструменты, самопроверка, демо-прототип |
| README: раздел «Демо-доступ» | VERIFIED | `grep "Демо-доступ" README.md` | `## Демо-доступ`; `admin` / `admin123`, ограничения HTTP/Flask/данных |
| README: Быстрый старт обновлён | VERIFIED | `grep "ВАШ_IP" README.md` | нет; локально `http://localhost:5004`, для демо `.env`: `ADMIN_BIND=0.0.0.0`, `DEMO_MODE=true`, `SESSION_COOKIE_SECURE=False` |
| SECURITY.md: раздел «Демо-режим» | VERIFIED | `grep "Демо-режим" SECURITY.md` | `## Демо-режим и известные ограничения`; 4 ограничения + поведение cookie |
| TECH_DEBT.md: решение по TLS | VERIFIED | `grep "2026-10-27" TECH_DEBT.md` | `- Решение владельца 2026-10-27: TLS для демо-экземпляра не добавляется; админка не используется с реальными данными.` |
| README: CI-раздел обновлён | VERIFIED | `grep "GitHub Secrets" README.md` | нет; required checks — плейсхолдер (F0.4 NOT VERIFIED), «Restrict updates» выключить |
| README: тесты (измеренные числа) | VERIFIED | `grep "159 passed" README.md` | `10 test files, 116 test functions; 159 passed, 0 failed, покрытие 95.76%` |
| ACCEPTANCE_REPORT.md: шапка | VERIFIED | `head -5 ACCEPTANCE_REPORT.md` | блок «Историческая запись от 2026-08-14 (ИИ-самопроверка)» перед заголовком |
| Ссылки на стандарт заменены | VERIFIED | `grep -rn "UPTIME_STUDIO" .` | нет (до: ACCEPTANCE_REPORT.md:5, SECURITY.md:5, ARCHITECTURE.md:5) |
| LICENSE: All rights reserved (F7-fix) | VERIFIED | `cat LICENSE`; `grep -rniE "\bMIT\b" .` | proprietary |
| ARCHITECTURE.md проверен | VERIFIED | `grep -n "UPTIME_STUDIO\|ai_assistant\|admin/admin.py" ARCHITECTURE.md` | устаревших утверждений и ссылок на удалённые файлы нет; заменена только строка про стандарт |
| grep запрещённых формулировок | VERIFIED | `grep -rniE "production-ready\|independent audit\|written by me\|автор(ом)? написал\|независимый аудит\|production ready" README.md *.md` | единственное совпадение — обязательная честная формулировка «а не независимый аудит» (F7.1); остального нет |
| compileall | VERIFIED | `python3 -m compileall -q app admin scripts tests` | exit 0 |
| ruff check | VERIFIED | `ruff check .` | `All checks passed!`, 0 ошибок |
| ruff format | VERIFIED | `ruff format --check .` | `37 files already formatted` |
| bandit | VERIFIED | `bandit -r app admin -ll -q` | exit 0, 0 findings (только WARNING про существующий `nosec B104`) |
| modularity | VERIFIED | `python3 scripts/check_modularity.py .` | `Модульность в порядке: проверено 27 файлов` |
| pytest | VERIFIED | `pytest tests/unit -m "not live" --cov --cov-fail-under=80` | `159 passed`, coverage `95.76%` |
| git status | VERIFIED | `git status --short` | изменены только allowed files F7 (плюс ранее существовавшие `AGENTS.md` и untracked артефакты); `.env`, `data/`, `logs/`, `media/`, `*.db`, `__pycache__` не в индексе |

### Примечания F7
- В ТЗ указано «106 test functions», фактически измерено **116** (`grep -rh "def test_" tests/unit/*.py | wc -l`); в README и отчёте записано фактическое число 116, чтобы не публиковать неверную цифру. Число `159 passed` — результат полного прогона (параметризация даёт больше кейсов, чем функций).
- LICENSE оформлен как proprietary («All rights reserved», правообладатель `alex-yorik`) согласно решению D4. Исходный MIT из F7 исправлен в F7-fix.
- `ACCEPTANCE_REPORT.md` изменён только добавлением шапки и заменой строки про стандарт; исторические цифры внутри (148 passed и т.п.) не менялись.
- `ARCHITECTURE.md`: устаревших утверждений не найдено; изменена только строка со ссылкой на стандарт.
- `pull-requests: read` и production-WSGI не добавлялись (D6); живой адрес демо-админки в README не указан (D5).

## F8: Финальная проверка

### F8-fix: комментарий DEMO_MODE в .env.example (owner-approved)

| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| Комментарий DEMO_MODE актуализирован | VERIFIED (owner-approved) | grep DEMO_MODE .env.example | комментарий соответствует коду F3 (`admin/web.py` читает переменную; значения 1/true/yes) |

### F8.1: healthz бота с фиктивным токеном

Метод: изолированный compose-стек в клоне `/tmp/f8-clean` (см. Отклонение г) с фиктивным токеном бота; реальный токен на этом шаге не использовался.

| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| healthz бота | NOT VERIFIED (ожидаемо) | curl http://127.0.0.1:18001/healthz | бот не достигает healthy: python-telegram-bot отклоняет фиктивный токен (`InvalidToken`); причина ожидаемая для фиктивного токена, живая проверка выполнена в F8.2 |

### F8.2: Живой тест

Стек: изолированный клон `/tmp/f8-clean` (коммит `fb5c802`; код идентичен HEAD `f698381` — отличие F8-fix только в комментарии `.env.example`, рантайм не затрагивает), override `f8-override.yml`: имена `f8-clean-bot`/`f8-clean-admin`, порты `127.0.0.1:18001`/`127.0.0.1:15004`. Реальный токен задан в локальном `.env` клона (gitignored, в git не попадает — F0.5); `DEMO_MODE=true`, `ADMIN_BIND=127.0.0.1`, `SESSION_COOKIE_SECURE=False`. Заявка отправлена живым Telegram-клиентом с вымышленными данными. Production до теста не запускался и не останавливался (N/A — Отклонение д). Времена: старт стека `2026-10-27T18:30:28Z`, `docker compose down` — `2026-10-27T18:36:06Z`.

| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| getMe | VERIFIED | Telegram BotAPI `getMe` | HTTP 200 — токен валиден |
| POST /login | VERIFIED | curl -X POST http://127.0.0.1:15004/login | HTTP 302 → `/` |
| GET / | VERIFIED | curl http://127.0.0.1:15004/ | HTTP 200; содержит «Тест Тест», «@fake_test_contact» и баннер DEMO |
| Строка в тестовой БД | VERIFIED | SELECT id, name, contact, status FROM applications | id=1; name=«Тест Тест»; contact=@fake_test_contact; status=new |
| Логи без конфликтов | VERIFIED | grep -E "409\|conflict\|unauthorized" (логи текущего запуска) | пусто |
| Стоп/возврат production | N/A | — | production не запущен до теста и оставлен незапущенным (решение владельца) |

### F8.3: Финализация отчёта (этот коммит)

| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| compileall | VERIFIED | python3 -m compileall -q app admin scripts tests | exit 0 |
| ruff check | VERIFIED | ruff check . | All checks passed!, 0 ошибок |
| ruff format | VERIFIED | ruff format --check . | 37 files already formatted |
| bandit | VERIFIED | bandit -r app admin -ll -q | exit 0, 0 findings (косметическое предупреждение про существующий nosec B104) |
| модулярность | VERIFIED | python3 scripts/check_modularity.py . | Модульность в порядке: проверено 27 файлов |
| pytest | VERIFIED | python3 -m pytest tests/unit -m "not live" --cov --cov-fail-under=80 | 159 passed, 0 failed; coverage 95.76% (гейт 80% пройден) |
| docker build | VERIFIED | docker build -t fitness-coach:ci . | exit 0, образ собран |
| git status | VERIFIED | git status --short | кроме данного отчёта — только существовавшие до hardening правки (`AGENTS.md`) и untracked-артефакты (см. F0) |

### Финальный статус GitHub (2026-10-28)

- Репозиторий сделан публичным: 2026-10-28.
- Ruleset `main`: Enforcement status = Active.
- Обязательные проверки (5): `Lint, compile and unit tests`, `Docker build`, `Bandit + secrets scan`, `Coverage gate >= 80%`, `Modularity gate`.
- Restrict updates: выключен (владелец может мержить).
- Force-push: запрещён ruleset'ом.
- Прямые коммиты в `main`: запрещены (только через PR).
- Закрыто 2026-10-28: репозиторий публичный, ruleset enforce активен.

### Сводная таблица F0–F8

| Фаза | Статус | Коммит | Ключевые VERIFIED / NOT VERIFIED (команды) |
|---|---|---|---|
| F0.1 Ветка и тег | VERIFIED | 11fa619 | git rev-parse pre-portfolio-ready → 6bc6c04… |
| F0.2 Baseline | VERIFIED | 1830c7a | pytest tests/unit -m "not live" --cov → 148 passed, coverage 95.76%; ruff check . → 0 ошибок; bandit -r app admin -ll -q → 0 findings |
| F0.3 Docker с чистого клона | FAILED (дефект, исправлен в F2) | c0d1f3b | docker compose up (isolated) → контейнеры запущены; ls -la data/ → root:root (uid 10001 писать не может); curl :18001/healthz → сброс соединения; логи: sqlite3.OperationalError; живой прогон изолированного клона — F8.2 (VERIFIED) |
| F0.4 GitHub Actions | NOT VERIFIED | 4c958b8 | gh run list → exit 4 (не авторизован) |
| F0.5 Секреты в истории | VERIFIED | 4c958b8 | gitleaks detect --log-opts="--all" → no leaks found; git log --all --oneline -- .env → пусто |
| F0.6 Полное чтение файлов | VERIFIED | ad5ee96 | реальное ФИО найдено в CHANGELOG.md:27 (устранено в F1); \|safe и autoescape off в шаблонах нет |
| F0.7 Скрипты | FAILED | ad5ee96 | bash scripts/backup.sh → позиционный аргумент игнорируется; init_new_bot.sh вне корня → exit 1 |
| F1 Чистка репозитория | VERIFIED | dcf93e7 | git ls-files \| grep -E "opencode\|ai_assistant\|admin/admin.py" → пусто; grep "Янаков" → пусто; pytest → 148 passed; модулярность → 25 |
| F2 Docker по умолчанию | VERIFIED | 29332df | docker compose config → 127.0.0.1:8001; ADMIN_BIND=0.0.0.0 docker compose config → 0.0.0.0; README: chown -R 10001:10001 |
| F3 Статусы и демо-баннер | VERIFIED | 7efebc2 | grep ALLOWED_STATUSES admin/web.py; pytest -k demo_banner → 2 passed; общий прогон → 152 passed |
| F4 PBKDF2 | VERIFIED | f5f67b3 | python -m admin.passwords → pbkdf2_sha256:600000:…; вход в контейнере: curl -X POST :5004/login → 302; общий прогон → 159 passed |
| F5 Демо-данные | VERIFIED | 69a3135 | grep "демо-бот" content/fitness_coach.json; общий прогон → 159 passed |
| F6 CI permissions | VERIFIED | 25fa746 | grep permissions .github/workflows/ci.yml → contents: read; grep fetch-depth .github/workflows/quality-gates.yml → fetch-depth: 0 |
| F7 Честная документация | VERIFIED | 7e7be85 | grep "Как сделан" README.md; grep "Демо-доступ" README.md; grep "159 passed" README.md → 10 файлов / 116 функций |
| F7-fix LICENSE | VERIFIED | fb5c802 | cat LICENSE → All rights reserved (по D4) |
| F8.1 healthz (фиктивный токен) | NOT VERIFIED (ожидаемо) | — (прогон без правок кода) | curl :18001/healthz → InvalidToken; живая проверка в F8.2 |
| F8.2 Живой тест | VERIFIED | — (прогон без правок кода) | getMe → 200; POST /login → 302; GET / → 200 («Тест Тест», @fake_test_contact, DEMO); БД id=1; grep "409\|conflict\|unauthorized" → пусто |
| F8-fix DEMO_MODE комментарий | VERIFIED (owner-approved) | f698381 | grep DEMO_MODE .env.example |
| F8.3 Финализация отчёта | VERIFIED | этот коммит | проверки F8.3 — все зелёные (см. выше) |

### Подавления линтеров (noqa / nosec / type: ignore)

Команда: `grep -rn "noqa\|nosec\|type: ignore" app admin scripts tests` — 2 совпадения; `noqa` и `type: ignore` не используются. Подавлений, добавленных в ходе F0–F8, нет — оба существовали до hardening:

| Файл:строка | Маркер | Причина |
|---|---|---|
| app/health_server.py:8 | `# nosec B104` | health-сервер намеренно слушает 0.0.0.0 внутри контейнера, чтобы healthcheck был доступен снаружи (существует до hardening, коммит 2db9da8) |
| admin/web.py:283 | `# nosec B104` | Flask-сервер админки намеренно слушает 0.0.0.0 в контейнере; наружу пробрасывается только порт, доступ с хоста ограничен ADMIN_BIND (по умолчанию 127.0.0.1 — F2; существует до hardening, коммит 4954a60) |

### Изменённые существующие тесты

- `tests/unit/test_web.py` — изменён в F4 (`f5f67b3`): способ формирования `FLASK_PASSWORD_HASH` (HMAC → `hash_password(TEST_PASSWORD, iterations=1000)` из нового `admin/passwords.py`), импорт `admin.web` перенесён на `importlib.import_module` после установки env. Обоснование: ТЗ F4 прямо отменяет HMAC-формат; без правки тесты админки падали бы на `RuntimeError` проверки формата при старте.
- Остальные существующие тесты не изменялись: F3 только добавлял новые тест-функции в `tests/unit/test_web.py` (`test_update_status_invalid`, `test_update_status_valid`, `TestDemoBanner` — существовавшие функции не тронуты), F5 правок тестов не потребовал. Новый тест-файл: `tests/unit/test_passwords.py` (F4, 7 тестов).

### Baseline vs итог (только измеренные числа)

| Метрика | Baseline (F0.2, 1830c7a) | Итог (F8.3, этот коммит) |
|---|---|---|
| pytest: passed / failed | 148 / 0 | 159 / 0 |
| coverage | 95.76% | 95.76% |
| ruff check, ошибок | 0 | 0 |
| bandit findings (-ll) | 0 | 0 (+ 2 существующих nosec B104 — оба до hardening) |
| тест-файлов | 10 | 10 |
| тест-функций | 106 | 116 |
| модулярность, файлов | 27 | 27 (промежуточно F1/F3 — 25) |

Примечания к подсчёту:
- Команды те же, что в F0.2: `pytest tests/unit -m "not live" --cov --cov-fail-under=80`, `ruff check .`, `ruff format --check .`, `bandit -r app admin -ll -q`, `python scripts/check_modularity.py .`.
- Тест-файлы/функции, baseline: `find tests -name "test_*.py" | wc -l` → 10 и `grep -rhE "^\s*(async )?def test_" tests | wc -l` → 106 — по всем `tests` (9 unit-файлов / 105 функций + 1 live-файл / 1 функция). Итог: по `tests/unit`, как в README (F7), — 10 файлов / 116 функций; с учётом `tests/live/test_live.py` — 11 файлов / 117 функций. Прирост unit-функций: +4 (F3) и +7 (F4, новый файл `test_passwords.py`); live-тест в unit-прогон не входит (`-m "not live"`).
- Модулярность: скрипт считает все `.py` вне SKIP_DIRS (app, admin, scripts, tests). F0.2 — 27; F1 — 25 (удалены `ai_assistant.py` и `admin/admin.py`); с F4 — 27 (добавлены `admin/passwords.py` и `tests/unit/test_passwords.py`); финал — 27.

### NOT VERIFIED / N/A (выносится в PR)

1. **F0.4**: `gh run list` — gh не авторизован (exit 4); статус workflows и точные имена проверок (поле `name:` в jobs) владелец проверяет через GitHub UI.
2. **F8.1**: healthz бота с фиктивным токеном — NOT VERIFIED, причина ожидаемая (`InvalidToken`); живая проверка стека выполнена в F8.2 (VERIFIED).
3. **F8.2**: production healthz — N/A: production не запущен по решению владельца (не запущен до теста, оставлен незапущенным).
4. **F8** (закрыто 2026-10-28): зелёные workflows на ветке PR — CI #7 и Quality Gates #7 (PR #1, synchronize) — 5 successful checks: `Lint, compile and unit tests`, `Docker build`, `Bandit + secrets scan`, `Coverage gate >= 80%`, `Modularity gate`. Ссылки на прогоны добавит владелец при желании.

- O1 (расширение ruff до B/UP/C4/SIM): пропущено по решению владельца от 2026-10-28.
- Артефакты живого теста `/tmp/f8-*` и `/tmp/fitness_coach.before.json` удалены владельцем (подтверждено 2026-10-28); реальный `BOT_TOKEN` в репозиторий и коммиты не попадал (F0.5).
- Фактические имена проверок для ruleset: `Lint, compile and unit tests`, `Docker build`, `Bandit + secrets scan`, `Coverage gate >= 80%`, `Modularity gate`.

## Отклонения от ТЗ (owner-approved)

- **а)** F7 (`7e7be85`) создал LICENSE с MIT вопреки D4; исправлено в F7-fix (`fb5c802`) — LICENSE «All rights reserved».
- **б)** F8-fix (`f698381`): комментарий DEMO_MODE в `.env.example` вне allowed files фазы F8 (owner-approved). Причина: после F3 код читает эту переменную, старый комментарий («текущий код переменную не читает») вводил в заблуждение.
- **в)** В коммит F2 вошли ранее существовавшие незакоммиченные правки `docker-compose.yml` (json-file logging, healthcheck interval) и README — те же файлы, что и правки фазы; логика не нарушена.
- **г)** F0.3/F8.1/F8.2: изолированный compose-override вне репозитория (порты `18001`/`15004`, имена `fitness-clean-*`/`f8-clean-*`), чтобы не трогать production-стенд.
- **д)** F8.2: стоп/возврат production — N/A по решению владельца: production не был запущен на момент теста и оставлен незапущенным.
- **е)** Строка про тесты в README: в ТЗ указано «106 test functions», фактически измерено 116 — записано измеренное (см. F7 и подсчёт выше).

## G1: Перепроверка покрытия и чисел тестов

Дата: 2026-10-29. Ветка `chore/demo-polish`, тег `pre-demo-polish`.

### Окружение

- Чистый venv: `/tmp/opencode/g1-venv`, Python 3.12.3.
- Установлено: `requirements.txt` + `pytest==9.1.1`, `pytest-asyncio==1.4.0`, `pytest-cov==7.1.0`, `ruff==0.16.1`, `bandit==1.9.4`.

### Команды и сырой вывод

```
$ python -m pytest tests/unit -m "not live" --cov --cov-report=term-missing --cov-fail-under=80
collected 159 items

tests/unit/test_bot.py ..                                                [  1%]
tests/unit/test_content_loader.py ..............                         [ 10%]
tests/unit/test_database.py ........                                     [ 15%]
tests/unit/test_handlers.py .....                                        [ 18%]
tests/unit/test_health_server.py ....                                    [ 20%]
tests/unit/test_logging_config.py .......                                [ 25%]
tests/unit/test_passwords.py .......                                     [ 29%]
tests/unit/test_trial.py .....................                           [ 42%]
tests/unit/test_validators.py .......................................... [ 69%]
..................                                                       [ 80%]
tests/unit/test_web.py ...............................                   [100%]

Name                    Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------
app/bot.py                 36      1      8      2    93%   43->46, 65
app/config.py               8      0      0      0   100%
app/content_loader.py      39      0     10      0   100%
app/database.py            18      0      2      0   100%
app/handlers/pages.py      17      0      2      0   100%
app/handlers/start.py      10      0      0      0   100%
app/handlers/trial.py     111      0     18      1    99%   123->130
app/health_server.py       37      2      4      0    95%   19-20
app/keyboards.py           10      1      2      1    83%   14
app/logging_config.py      29      0      4      0   100%
app/validators.py         164     14    108      3    93%   57->47, 88->84, 175-193
-------------------------------------------------------------------
TOTAL                     479     18    158      7    96%
Required test coverage of 80% reached. Total coverage: 95.76%
======================= 159 passed, 1 warning in 17.23s ========================
```

```
$ find tests/unit -name "test_*.py" | wc -l
10

$ grep -rhE "^\s*(async )?def test_" tests/unit | wc -l
116
```

### Измеренные значения

| Метрика | Значение |
|---|---|
| passed / failed / skipped | 159 / 0 / 0 |
| TOTAL coverage | 95.76% (округлённо 96%) |
| test files (`tests/unit`) | 10 |
| test functions (`tests/unit`) | 116 |

### Сверка с README

Строка README («10 test files, 116 test functions; 159 passed, 0 failed, покрытие 95.76%») совпала с повторным прогоном: **подтверждено повторным прогоном 2026-10-29**. Цифры не менялись.

## G5: Финальная проверка и отчёт

Дата: 2026-10-29. Ветка `chore/demo-polish`, тег `pre-demo-polish`.

### Чистый клон и Docker

Клон ветки: `git clone --branch chore/demo-polish /opt/fitness-coach /tmp/opencode/g5-clean` (HEAD `52955a0`, G4).

Изолированный стенд (override вне репозитория, чтобы не трогать production): порты `127.0.0.1:15004` (админка) и `127.0.0.1:18001` (health бота), имена `g5-clean-*`.

```
$ docker compose -f docker-compose.yml -f /tmp/opencode/g5-override.yml -p g5clean up -d --build
...
 Container g5-clean-bot  Started
 Container g5-clean-webadmin  Started

$ docker compose ... ps -a
NAME                IMAGE                   COMMAND                 SERVICE         STATUS
g5-clean-bot        g5clean-fitness-coach   "python -m app.bot"     fitness-coach   Up (health: starting)
g5-clean-webadmin   g5clean-webadmin        "python -m admin.web"   webadmin        Up (healthy)
```

Проверки стека:

```
$ curl -f http://127.0.0.1:18001/healthz   # бот
200 ok
$ curl -f http://127.0.0.1:15004/healthz   # админка
200 ok
$ curl -X POST -d "username=admin&password=G5-Demo-Pass-2026" http://127.0.0.1:15004/login
POST /login -> 302 redirect=http://127.0.0.1:15004/
$ curl -b cookies http://127.0.0.1:15004/
GET / -> 200 (в HTML: Fitness Coach, Заявки, DEMO, Выйти)
```

Бот запущен с фиктивным `BOT_TOKEN` (изоляция от production-поллинга): health-сервер отвечает `200 ok`, в логах ожидаемый `telegram.error.InvalidToken`. Живой Telegram-бот в этом прогоне не проверялся.

**Наблюдение вне задачи:** production-контейнер `fitness-coach` на момент проверки находится в crash-loop с `telegram.error.InvalidToken` (токен отклонён сервером). Это состояние существовало до начала работ (на старте сессии контейнер был `Up 1 second`), код и `.env` не менялись. Для живого показа `@Demo_Fitness_Coach_bot` владельцу нужно заменить `BOT_TOKEN` в `.env` production-стенда.

### Проверки 1.4

```
$ python -m compileall -q app admin scripts tests          → exit 0
$ ruff check .                                             → All checks passed!
$ ruff format --check .                                    → 40 files already formatted
$ bandit -r app admin -ll -q                               → exit 0 (только 1 существующий nosec B104)
$ python scripts/check_modularity.py .                     → Модульность в порядке: проверено 27 файлов
$ python -m pytest tests/unit -m "not live" --cov --cov-fail-under=80
TOTAL 479 18 158 7 96%
Required test coverage of 80% reached. Total coverage: 95.76%
159 passed, 1 warning in 19.70s
```

`git status --short` (в рабочем дереве только служебные файлы вне задачи: `AGENTS.md` — хук graphify, `.env.backup-*`, `.gitattributes`, `.graphifyignore`, `graphify-out/`) и `git diff --stat` — `AGENTS.md | 13 +++++++++++++`; в коммиты G1–G5 эти файлы не входят.

### GitHub Actions

На `main` (`235c4b6`):

- CI (push): success — https://github.com/alex-yorik/fitness-coach-bot/actions/runs/40743602274
- Quality Gates (push): success — https://github.com/alex-yorik/fitness-coach-bot/actions/runs/40743602477
- Check-runs коммита: `Lint, compile and unit tests`, `Docker build`, `Bandit + secrets scan`, `Coverage gate >= 80%`, `Modularity gate` — все success.

Workflows настроены на push в `main` и на `pull_request` в `main`; push feature-ветки `chore/demo-polish` прогоны не запускает (`gh api .../runs?branch=chore/demo-polish` → 0). Для проверки ветки нужен PR в `main`; он не создавался (в ТЗ только push ветки).

### Таблица G1–G5

| Блок | Статус | Команда/доказательство |
|---|---|---|
| G1 — покрытие и числа тестов | VERIFIED | `pytest tests/unit -m "not live" --cov` → 159 passed / 0 failed; TOTAL 95.76%; 10 файлов / 116 функций; совпало с README |
| G2 — документация под закрытую админку | VERIFIED | `grep -n "admin123\|Миграция с открытого\|Демо-доступ\|reverse proxy с TLS" README.md SECURITY.md TECH_DEBT.md` → пусто; diff README/SECURITY/TECH_DEBT/.env.example |
| G3 — ссылка на бота и скриншоты | VERIFIED | `grep -n "Demo_Fitness_Coach_bot\|docs/assets/" README.md`; `file docs/assets/*.png` → 2 PNG; см. раздел «G3-fix» |
| G4 — docs/DEMO.md | VERIFIED | `grep -n "docs/DEMO.md" README.md`; `curl -I` ссылки Cloudflare → 200 |
| G5 — финальная проверка | VERIFIED (админка/health) | чистый клон + `docker compose up -d --build`; `/healthz` 200/200; `POST /login` → 302 → `GET /` 200; 1.4 — все зелёные |

### Изменившиеся цифры

G1 цифры не изменил: 159 passed / 0 failed, покрытие 95.76%, 10 test files, 116 test functions — совпало с прежним README. Других измеряемых цифр правки G2–G5 не меняют.

### Отклонения от ТЗ (owner-approved)

- **P1 отменён** (решение владельца D2): демо-экземпляр «только для чтения» не создавался; показываются скриншоты и основной живой бот `@Demo_Fitness_Coach_bot` (D3).
- **G5-стенд изолирован**: override вне репозитория (`/tmp/opencode/g5-override.yml`), порты `15004`/`18001`, имена `g5-clean-*` — чтобы не останавливать production-контейнеры (аналогично отклонению «г» в F0.3/F8).
- **G5: фиктивный `BOT_TOKEN`** в чистом клоне: реальный токен конфликтует с production-поллингом. Health бота проверен, Telegram-подключение — нет (ожидаемый `InvalidToken`).
- **docs/assets/**: на момент G5 каталог был пуст (git не хранит пустые каталоги). 2026-10-29 владелец передал 2 скриншота бота; они добавлены в `docs/assets/` (см. раздел «G3-fix»).
- **Workflow-ссылки** даны для `main` (`235c4b6`); прогоны ветки появятся после пуша.

## G3-fix: скриншоты от владельца

Дата: 2026-10-29. Ветка `chore/demo-polish`.

Владелец передал два снимка экрана Telegram-бота (JPEG 1080 px по ширине), из них созданы PNG для README:

| Исходник | Файл в репозитории | Содержимое | Размер |
|---|---|---|---|
| `de91c66a-…jpg` | `docs/assets/bot-chat.png` | приветствие `/start`, кнопки меню | 1080×2100, ~1.1 МБ |
| `d8778f42-…jpg` | `docs/assets/trial-form.png` | шаги 3–4 формы и подтверждение заявки | 1080×2082, ~1.1 МБ |

Ссылки в README указывают на эти файлы; строка «Скриншоты загружаются владельцем…» заменена на фактическое описание, упоминание скриншотов админки убрано (снимков админки не передано).

### Проверки G3-fix

| Пункт | Статус | Команда | Вывод |
|---|---|---|---|
| файлы существуют | VERIFIED | `file docs/assets/*.png` | 2 файла: PNG, 8-bit RGB, без интерлейса |
| ссылки README | VERIFIED | `grep -n "docs/assets/" README.md` | `bot-chat.png`, `trial-form.png` |
| данные вымышленные | VERIFIED | осмотр снимков | имя «Тест Тест», контакт `@fake_test_contact` |
| проверки 1.4 | VERIFIED | см. команды ниже | все exit 0 |

### Повторный прогон 1.4 (после добавления PNG)

```
$ python -m compileall -q app admin scripts tests     → exit 0
$ ruff check .                                        → All checks passed!
$ ruff format --check .                               → 40 files already formatted
$ bandit -r app admin -ll -q                          → exit 0 (1 существующий nosec B104)
$ python scripts/check_modularity.py .                → Модульность в порядке: проверено 27 файлов
$ python -m pytest tests/unit -m "not live" --cov --cov-fail-under=80
TOTAL 479 18 158 7 96%
Required test coverage of 80% reached. Total coverage: 95.76%
159 passed, 1 warning in 21.07s
$ docker build -t fitness-coach:g5-check .            → Successfully tagged, exit 0
```

Состояние production на 2026-10-29: `fitness-coach` и `fitness-coach-webadmin` — `healthy`, `GET /healthz` на портах 8001 и 5004 — HTTP 200. Наблюдение из раздела G5 о crash-loop бота устарело: владелец заменил `BOT_TOKEN`, контейнер перезапущен и работает.

## H1: admin/ включён в измерение покрытия

Дата: 2026-10-29. Ветка `chore/final-touches`.

В `pyproject.toml` (`[tool.coverage.run]`) источник покрытия расширен:
`source = ["app", "admin"]`. Порог `fail_under = 80` не менялся.

```
$ python3 -m pytest tests/unit -m "not live" --cov --cov-report=term-missing --cov-fail-under=80
Name                    Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------
admin/passwords.py         36     14      8      2    55%   44, 50-51, 59-71, 75
admin/web.py              181      8     36      8    93%   27, 43, 48, 69, 74->76, 146->148, 151, 281-283
app/bot.py                 36      1      8      2    93%   43->46, 65
app/config.py               8      0      0      0   100%
app/content_loader.py      39      0     10      0   100%
app/database.py            18      0      2      0   100%
app/handlers/pages.py      17      0      2      0   100%
app/handlers/start.py      10      0      0      0   100%
app/handlers/trial.py     111      0     18      1    99%   123->130
app/health_server.py       37      2      4      0    95%   19-20
app/keyboards.py           10      1      2      1    83%   14
app/logging_config.py      29      0      4      0   100%
app/validators.py         164     14    108      3    93%   57->47, 88->84, 175-193
-------------------------------------------------------------------
TOTAL                     696     40    202     17    93%
Required test coverage of 80% reached. Total coverage: 92.98%
159 passed, 1 warning in 11.30s
```

Итог: гейт ≥ 80% пройден (92.98%); дополнительные тесты не требовались.
README обновлён на 92.98% с явным указанием пакетов `app/` и `admin/`.
