# 🏋️ Fitness Coach Bot

[![CI](https://github.com/alex-yorik/fitness-coach-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/alex-yorik/fitness-coach-bot/actions/workflows/ci.yml)
[![Quality Gates](https://github.com/alex-yorik/fitness-coach-bot/actions/workflows/quality-gates.yml/badge.svg)](https://github.com/alex-yorik/fitness-coach-bot/actions/workflows/quality-gates.yml)

Telegram-бот фитнес-тренера с формой записи на пробную тренировку, мини-CRM и веб-админкой.

## ✨ Особенности

- Визитка тренера с информацией об услугах и ценах
- Форма записи на пробную тренировку прямо в боте
- Мини-CRM для управления заявками в Telegram
- Веб-админка с авторизацией и выгрузкой в Excel
- Healthcheck и ротация логов (см. `docker-compose.yml`, `app/health_server.py`)

## 🚀 Быстрый старт

1. Склонировать репозиторий и скопировать шаблон окружения:

       cp .env.example .env

2. Заполнить `.env`:

       # Telegram
       BOT_TOKEN=ваш_токен_от_BotFather
       ADMIN_CHAT_ID=telegram_id_тренера

       # Веб-админка
       FLASK_USERNAME=admin
       # хеш пароля: hmac.new(SECRET_KEY, пароль, sha256)
       FLASK_PASSWORD_HASH=<сгенерировать, см. ниже>
       SECRET_KEY=<случайный_64-символьный_hex>

       # True — если админка за TLS/HTTPS (fail-closed), False — только локально по HTTP
       SESSION_COOKIE_SECURE=True

       # БД и логи
       DATABASE_PATH=/app/data/database.db
       LOG_PATH=/app/logs/bot.log
       WEB_LOG_PATH=/app/logs/web.log
       HEALTH_PORT=8001

3. Сгенерировать хеш пароля админки (пароль хранится только в виде хеша,
   привязанного к `SECRET_KEY`):

       python3 -c "from dotenv import load_dotenv; load_dotenv(); import hmac,hashlib,os; print(hmac.new(os.environ['SECRET_KEY'].encode(), b'ваш_пароль', hashlib.sha256).hexdigest())"

   Вывод записать в `FLASK_PASSWORD_HASH`.

4. Запустить:

       docker-compose up -d --build

5. Проверить статус и health:

       docker-compose ps
       curl -f http://localhost:8001/healthz   # бот: 200 ok
       curl -f http://localhost:5004/healthz   # админка: 200 ok

## 🔐 Миграция с открытого пароля

Если в `.env` ещё остался `FLASK_PASSWORD` в открытом виде, сгенерируйте хеш
из него и удалите ключ:

    python3 -c "from dotenv import load_dotenv; load_dotenv(); import hmac,hashlib,os; print(hmac.new(os.environ['SECRET_KEY'].encode(), os.environ['FLASK_PASSWORD'].encode(), hashlib.sha256).hexdigest())"

Затем в `.env`: `FLASK_PASSWORD_HASH=<вывод>` и удалить строку `FLASK_PASSWORD=...`.

## 📁 Структура проекта

    FitnessCoach/
    ├── app/
    │   ├── bot.py              # точка входа бота, регистрация хендлеров
    │   ├── config.py           # конфигурация из .env
    │   ├── database.py         # SQLite (WAL), init_db
    │   ├── keyboards.py
    │   ├── content_loader.py   # загрузка/валидация JSON-контента
    │   ├── validators.py       # валидация контента и ответов формы
    │   ├── logging_config.py   # ротация логов (10 МБ × 5)
    │   ├── health_server.py    # GET /healthz (порт 8001)
    │   └── handlers/
    │       ├── start.py
    │       ├── pages.py
    │       └── trial.py        # форма записи (ConversationHandler)
    ├── admin/
    │   ├── web.py              # Flask-админка (порт 5004)
    │   └── templates/
    ├── content/
    │   └── fitness_coach.json
    ├── scripts/
    │   ├── backup.sh           # атомарный бэкап SQLite (ротация 14 дней)
    │   └── check_modularity.py # гейт: файл ≤500, функция ≤50 строк
    ├── tests/
    │   ├── conftest.py
    │   ├── unit/               # unit-тесты (валидаторы, БД, хендлеры, web, ...)
    │   └── live/               # live-тесты Telegram API (@pytest.mark.live)
    ├── .env.example
    ├── docker-compose.yml
    ├── Dockerfile
    ├── ARCHITECTURE.md         # поток данных, хранилище, ключевые решения
    ├── SECURITY.md             # модель угроз и контрмеры
    ├── TECH_DEBT.md            # технические долги
    ├── CHANGELOG.md            # git-cliff из conventional commits
    ├── ACCEPTANCE_REPORT.md    # финальная приёмка по standard of quality
    └── cliff.toml

## 🌐 Веб-админка

Доступна по адресу: **http://ВАШ_IP:5004**

Логин и пароль задаются в `.env` (логин `FLASK_USERNAME`, пароль — только в виде
хеша `FLASK_PASSWORD_HASH`).

Возможности:
- Просмотр всех заявок
- Фильтрация по статусам (новые / в работе / завершённые)
- Смена статусов и удаление
- Выгрузка в Excel

## 🤖 CRM команды в Telegram

| Команда | Описание |
|---|---|
| /crm | Новые заявки |
| /all | Все заявки |
| /all new | Только новые |
| /all in_progress | В работе |
| /all done | Завершённые |
| /stats | Статистика |

## 📊 Статусы заявок

| Статус | Значение |
|---|---|
| new | 🆕 Новая заявка |
| in_progress | ⏳ В работе |
| done | ✅ Завершена |

## 🧪 Тесты

    # Быстрый прогон (unit-тесты, без сети)
    python -m pytest tests/unit -m "not live"

    # С coverage-гейтом (>=80%)
    python -m pytest tests/unit -m "not live" --cov --cov-fail-under=80

Live-тесты, требующие реальный Telegram API, помечены `@pytest.mark.live`
и по умолчанию пропускаются. Запуск только вручную:

    RUN_LIVE_TESTS=1 python -m pytest -m live

## 🤖 CI/CD

Проверки качества автоматически запускаются на каждый push/PR в `main`
(GitHub Actions, Python 3.12, < 5 мин):

| Workflow | Что проверяет |
|---|---|
| `ci.yml` | ruff check + format, py_compile всех файлов, unit-тесты, docker build |
| `quality-gates.yml` | bandit (`-ll`, 0 HIGH), secrets-скан (gitleaks), coverage ≥ 80%, модульность (`scripts/check_modularity.py`) |

В CI запускаются только unit-тесты (`-m "not live"`), live-тесты — никогда.

Рекомендуется включить branch protection для `main` с required checks
(`test`, `docker-build`, `security`, `coverage`, `modularity`) и хранить
секреты `BOT_TOKEN`, `ADMIN_CHAT_ID`, `FLASK_PASSWORD_HASH`, `SECRET_KEY`
в GitHub Secrets.

### 📝 Changelog

`CHANGELOG.md` генерируется из conventional commits через `git-cliff`
(конфиг `cliff.toml`, разделы Added/Changed/Fixed/Security). Регенерировать:

    git-cliff -o CHANGELOG.md

## 🛠 Docker команды

    # Статус контейнеров
    docker-compose ps

    # Логи бота
    docker logs fitness-coach --tail=30

    # Логи веб-админки
    docker logs fitness-coach-webadmin --tail=30

    # Перезапуск
    docker-compose restart fitness-coach

    # Пересборка после изменений
    docker-compose up -d --build

### Healthcheck

Оба сервиса имеют `healthcheck` в `docker-compose.yml` (curl на `/healthz`,
интервал 30s, start_period 15s). Health-эндпоинты проверяют доступность БД:

- бот: `http://localhost:8001/healthz`
- админка: `http://localhost:5004/healthz`

## 📝 Обновление контента

    nano content/fitness_coach.json
    docker-compose restart fitness-coach

## 🔧 Стек

- Python 3.12
- python-telegram-bot
- SQLite (WAL)
- Flask + flask-limiter
- openpyxl
- Docker + Docker Compose
- git-cliff (changelog)

## ℹ️ Быстрая справка

| Параметр | Значение |
|---|---|
| 📦 Контейнер бота | `fitness-coach` |
| 🌐 Контейнер админки | `fitness-coach-webadmin` |
| 🔌 Порт админки | **5004** |
| ❤️ Health-порт бота | **8001** |
| 👤 Логин | `admin` (из `.env`) |
| 🔑 Пароль | хеш (см. `FLASK_PASSWORD_HASH`) |
| 🗄 БД | `/app/data/database.db` (volume `./data`) |
