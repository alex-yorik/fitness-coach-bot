# 🏋️ Fitness Coach Bot

Telegram-бот фитнес-тренера с формой записи на пробную тренировку, мини-CRM и веб-админкой.

## ✨ Особенности

- Визитка тренера с информацией об услугах и ценах
- Форма записи на пробную тренировку прямо в боте
- Мини-CRM для управления заявками в Telegram
- Веб-админка с авторизацией и выгрузкой в Excel

## 📁 Структура проекта

    FitnessCoach/
    ├── app/
    │   ├── bot.py
    │   ├── config.py
    │   ├── database.py
    │   ├── keyboards.py
    │   ├── content_loader.py
    │   └── handlers/
    │       ├── start.py
    │       ├── pages.py
    │       └── trial.py
    ├── admin/
    │   ├── admin.py
    │   ├── web.py
    │   └── templates/
    ├── content/
    │   └── fitness_coach.json
    ├── data/
    │   └── database.db
    ├── media/
    ├── templates/
    ├── tests/
    │   ├── conftest.py
    │   ├── unit/          # unit-тесты (validators, database, trial, web, ...)
    │   └── live/          # live-тесты Telegram API (@pytest.mark.live)
    ├── .env
    ├── docker-compose.yml
    ├── Dockerfile
    ├── ai_assistant.py
    ├── init_new_bot.sh
    └── requirements.txt

## 🚀 Установка и запуск

1. Заполнить `.env`:

        BOT_TOKEN=ваш_токен_от_BotFather
        ADMIN_CHAT_ID=telegram_id_тренера
        FLASK_USERNAME=admin
        SECRET_KEY=случайный_64-символьный_hex
        FLASK_PASSWORD_HASH=<см. ниже>
        DATABASE_PATH=/app/data/database.db

2. Сгенерировать хеш пароля админки (вместо хранения в открытом виде):

        cd /opt/fitness-coach
        python3 -c "from dotenv import load_dotenv; load_dotenv(); import hmac,hashlib,os; print(hmac.new(os.environ['SECRET_KEY'].encode(), b'ваш_пароль', hashlib.sha256).hexdigest())"

   Значение записать в `FLASK_PASSWORD_HASH`.

3. Запустить:

        docker-compose up -d --build

## 🔐 Миграция с открытого пароля

Если в `.env` ещё остался `FLASK_PASSWORD` в открытом виде, сгенерируйте
хеш из него и удалите ключ:

    python3 -c "from dotenv import load_dotenv; load_dotenv(); import hmac,hashlib,os; print(hmac.new(os.environ['SECRET_KEY'].encode(), os.environ['FLASK_PASSWORD'].encode(), hashlib.sha256).hexdigest())"

Затем в `.env`: `FLASK_PASSWORD_HASH=<вывод>` и удалить строку `FLASK_PASSWORD=...`.

## 🌐 Веб-админка

Доступна по адресу: **http://ВАШ_IP:5004**

Логин и пароль задаются в `.env` (по умолчанию логин `admin`, пароль —
только в виде хеша `FLASK_PASSWORD_HASH`).

Возможности:
- Просмотр всех заявок
- Фильтрация по статусам (новые / в работе / завершённые)
- Смена статусов
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
    pytest

    # С coverage-гейтом (>=80%)
    pytest --cov --cov-fail-under=80

Live-тесты, требующие реальный Telegram API, помечены `@pytest.mark.live`
и по умолчанию пропускаются. Запуск только вручную:

    RUN_LIVE_TESTS=1 pytest -m live

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

## 📝 Обновление контента

    nano content/fitness_coach.json
    docker-compose restart fitness-coach

## 🔧 Стек

- Python 3.12
- python-telegram-bot
- SQLite
- Flask
- openpyxl
- Docker + Docker Compose

## ℹ️ Быстрая справка

| Параметр | Значение |
|---|---|
| 📦 Контейнер бота | `fitness-coach` |
| 🌐 Контейнер админки | `fitness-coach-webadmin` |
| 🔌 Порт админки | **5004** |
| 👤 Логин | `admin` |
| 🔑 Пароль | хеш (задаётся в `.env`, см. `FLASK_PASSWORD_HASH`) |
