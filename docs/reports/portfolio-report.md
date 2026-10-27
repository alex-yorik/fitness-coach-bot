# Журнал ИИ-assisted инженерных правок
**Это не независимый аудит**

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
