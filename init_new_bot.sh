#!/usr/bin/env bash

set -e

TEMPLATE=""
CLIENT_NAME=""

for arg in "$@"; do
    case "$arg" in
        --template=*)
            TEMPLATE="${arg#*=}"
            ;;
        --name=*)
            CLIENT_NAME="${arg#*=}"
            ;;
    esac
done

if [ -z "$TEMPLATE" ] || [ -z "$CLIENT_NAME" ]; then
    echo "❌ Ошибка: нужно передать оба аргумента."
    echo ""
    echo "Пример:"
    echo "./init_new_bot.sh --template=fitness --name=ivan"
    exit 1
fi

TEMPLATE_FILE="templates/${TEMPLATE}.json"
TARGET_DIR="${CLIENT_NAME}bot"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Ошибка: шаблон не найден: $TEMPLATE_FILE"
    echo ""
    echo "Доступные шаблоны:"
    ls templates/*.json 2>/dev/null | sed 's|templates/||; s|.json||'
    exit 1
fi

if [ -e "$TARGET_DIR" ]; then
    echo "❌ Ошибка: папка уже существует: $TARGET_DIR"
    exit 1
fi

mkdir -p "$TARGET_DIR"

tar --exclude="./$TARGET_DIR" -cf - . | tar -xf - -C "$TARGET_DIR"

rm -rf "$TARGET_DIR/.git"

cp "$TARGET_DIR/.env.example" "$TARGET_DIR/.env"

cp "$TEMPLATE_FILE" "$TARGET_DIR/content/${CLIENT_NAME}.json"
rm -f "$TARGET_DIR/content/fitness_coach.json"

mkdir -p "$TARGET_DIR/media/about" "$TARGET_DIR/media/formats"

rm -f "$TARGET_DIR/data/database.db"

echo ""
echo "✅ Новый бот создан: $TARGET_DIR"
echo ""
echo "Что делать дальше:"
echo "1. Откройте файл $TARGET_DIR/.env и заполните BOT_TOKEN и ADMIN_CHAT_ID."
echo "2. Отредактируйте контент в файле $TARGET_DIR/content/${CLIENT_NAME}.json."
echo "3. Добавьте медиафайлы в папки $TARGET_DIR/media/about и $TARGET_DIR/media/formats."
echo "4. Перейдите в папку проекта:"
echo "   cd $TARGET_DIR"
echo "5. Запустите бота:"
echo "   docker-compose up -d --build"
echo ""
echo "Шаблон: $TEMPLATE"
echo "Клиент: $CLIENT_NAME"
echo ""
