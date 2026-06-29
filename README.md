## 📋 Доступные шаблоны

- teacher
- fitness
- beauty
- psychologist
- cafe

## 🚀 Быстрый старт через скрипт

Создать нового бота из шаблона:

```bash
./init_new_bot.sh --template=fitness --name=ivan
```

После создания заполните `.env`, отредактируйте JSON-файл в папке `content/` и запустите проект через `docker-compose`.

## ✅ Валидация контента

Проверить структуру JSON-контента:

```bash
python app/validators.py content/teacher.json
```
