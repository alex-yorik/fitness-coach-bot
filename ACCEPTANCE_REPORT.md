# Отчёт о приёмке (Этап 7) — Fitness Coach Bot

Дата: **2026-08-14**
Коммит: **cadeaff (Stage 5) + правки приёмки** (см. ниже)
Стандарт качества: `UPTIME_STUDIO_QUALITY_STANDARD.md` (проект строился по нему с Этапа 0)

---

## 1. Локальный прогон

| Проверка | Команда | Результат |
|---|---|---|
| Тесты + coverage-гейт | `pytest --cov --cov-fail-under=80` | ✅ **148 passed**, coverage **95.76%** (гейт 80% пройден) |
| Линтер | `ruff check .` | ✅ **0 ошибок** («All checks passed!») |
| Форматтер | `ruff format --check .` | ✅ 33 файла отформатированы |
| Security-скан | `bandit -r app admin -ll` | ✅ **0 HIGH**, 0 Medium, 0 Low |
| Модульность | `python scripts/check_modularity.py .` | ✅ «Модульность в порядке: проверено 27 файлов» |
| Компиляция (CI-гейт) | `python3 -m py_compile app/*.py admin/*.py ...` | ✅ OK |

### Найденные и устранённые при приёмке дефекты

1. **`pytest` без `python -m` падал** (`ModuleNotFoundError: No module named 'app'`).
   CI запускал тесты через `python -m pytest` (добавляет CWD в `sys.path`), поэтому
   гейт «в проде» был завязан на способ вызова, а не на конфиг.
   **Исправление:** в `pyproject.toml` добавлен `pythonpath = ["."]` в
   `[tool.pytest.ini_options]` — теперь команда из задачи (`pytest --cov --cov-fail-under=80`)
   работает как написано.

2. **Bandit выходил с кодом 1 на новом `B104`** в `app/health_server.py:8` (добавлен в
   Этапе 5, в отличие от `admin/web.py:260`, где `nosec` был). Бинд на `0.0.0.0` намеренный —
   healthcheck в `docker-compose.yml` ходит снаружи контейнера на порт 8001.
   **Исправление:** добавлен `# nosec B104` с пояснением (форма комментария идентична
   `web.py:260`). Проверено: с `nosec` — 0 findings B104, без — 1; гейт `bandit -r app admin -ll`
   выходит с кодом 0. Бандит печатает косметическое предупреждение «nosec encountered ... no
   failed test» из-за формы `os.getenv(..., "0.0.0.0")` — на результат (exit 0) не влияет.

## 2. Docker-проверка

| Проверка | Команда | Результат |
|---|---|---|
| Пересборка | `docker-compose down && up -d --build` | ✅ успешно (образ пересобран) |
| Health | `docker ps` | ✅ **оба контейнера `healthy`** |
| Health-эндпоинт бота | `curl http://localhost:8001/healthz` | ✅ **200 OK** |
| Health-эндпоинт админки | `curl http://localhost:5004/healthz` | ✅ **200 OK** |
| Логи с ротацией | `ls -la logs/` | ✅ `bot.log` + `web.log` пишутся, `RotatingFileHandler` 10 МБ × 5 backup |
| Бот запущен | `docker logs fitness-coach` | ✅ «FitnessCoach запущен», health-запросы логируются |
| Админка: авторизация | `GET /` без сессии | ✅ 302 → `/login` |
| Админка: неверный пароль | `POST /login` | ✅ «Неверный логин или пароль» (fail-closed, rate-limit 5/min) |

Контейнеры работают от непривилегированного пользователя `appuser` (Dockerfile),
логи пишутся в отдельный volume `/app/logs`, не смешаны с кодом.

## 3. Сверка TECH_DEBT.md

- **Закрытые пункты — с датой и способом:** ✓
  - «Функции превышали лимит 50 строк» — закрыт **2026-08-14**, рефакторинг на
    хелперы подтверждён повторным прогоном check_modularity. Ссылки на строки в файле
    проверены по коду: `validators.py:118`, `admin/web.py:237`, `trial.py:150` — актуальны.
- **Открытые пункты — с планом и сроком:** ✓
  - HTTP без TLS → план (Caddy/reverse proxy + `SESSION_COOKIE_SECURE=True`), срок Q1 2027.
  - Прямой SQL без ORM → план (alembic при росте схемы), срок Q3 2026.
  - In-memory rate-limiter → план (Redis backend при >1 реплике), документировано в `SECURITY.md:95`.
- Противоречий с фактическим состоянием кода **нет** (проверены пути, декораторы, `nosec`).

## 4. Отчёт по пунктам §1–§7 стандарта качества

| § | Раздел стандарта | Статус | Реализация |
|---|---|---|---|
| §1 | Безопасность | ✅ Реализовано | Fail-closed (`SESSION_COOKIE_SECURE=True` по умолчанию, отсутствие кредов → `RuntimeError`); секреты только через `.env` (0 хардкода, gitleaks в CI); timing-safe (`hmac.compare_digest` для пароля и CSRF); rate-limit на `/login` (5/min); параметризованные SQL; `html.escape` + Jinja-autoescape (XSS); `sanitize_cell` для Excel (инъекции формул); `appuser` в Docker; `.dockerignore` исключает `.env`/`.git`. **Исключение (открытый долг):** TLS в проде — план в TECH_DEBT.md, срок Q1 2027. |
| §2 | Конкурентность и целостность данных | ✅ Реализовано | SQLite WAL + `busy_timeout=5000`, атомарные параметризованные операции, бэкап через `scripts/backup.sh` (атомарный, ротация 14 дней). Shared-state через read→modify→write поверх файла отсутствует. |
| §3 | Тесты | ✅ Реализовано | 148 unit-тестов (coverage 95.76%); live-тесты отделены маркером `@pytest.mark.live` и не блокируют обычный прогон; покрыты security-пути (auth, CSRF, rate-limit, инъекции) и бизнес-логика (валидация формы). Coverage-гейт 80% в CI. |
| §4 | CI/CD | ✅ Реализовано | 2 независимых workflow: `ci.yml` (ruff, py_compile, unit-тесты, docker build) и `quality-gates.yml` (bandit 0 HIGH, gitleaks, coverage ≥80%, модульность). Запуск на push/PR в `main`. |
| §5 | Модульность и code style | ✅ Реализовано | Гейт `scripts/check_modularity.py` (файл ≤500, функция ≤50 строк) в CI; ruff закреплён в `pyproject.toml` + pre-commit hook; слои разделены (handlers / admin / scripts / content). |
| §6 | Документация | ✅ Реализовано | `README.md`, `ARCHITECTURE.md`, `SECURITY.md`, `TECH_DEBT.md`, `CHANGELOG.md` (git-cliff из conventional commits, `cliff.toml`) — обновлены в том же PR. Пути в документах сверены с кодом, устаревших ссылок нет. |
| §7 | Наблюдаемость | ✅ Реализовано | Ротация логов (10 МБ × 5, `RotatingFileHandler`), отдельный volume `/app/logs`; health-эндпоинты `/healthz` (8001 — бот, 5004 — админка) + `healthcheck` в docker-compose; оба контейнера `healthy`. |

## 5. Критерии приёмки

- [x] pytest — 100% pass (148/148), coverage **95.76% ≥ 80%**
- [x] ruff — 0 ошибок (check + format)
- [x] bandit — **0 HIGH** (exit 0 по `-ll`)
- [x] check_modularity — OK (27 файлов)
- [x] docker health = **healthy** (оба сервиса)
- [x] /healthz — **200 OK** (8001 и 5004)
- [x] TECH_DEBT.md актуален (закрытые с датой, открытые с планом)
- [x] Отчёт о приёмке создан (данный файл)

## 6. Итог

**Приёмка пройдена.** Все критерии definition of done выполнены. В процессе приёмки
устранены два дефекта (вызов pytest и новый `B104` в health_server), после чего
все гейты зелёные локально и в Docker. Открытые пункты TECH_DEBT.md не блокируют
приёмку: причины задокументированы, сроки назначены.
