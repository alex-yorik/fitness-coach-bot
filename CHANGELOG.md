# Changelog

Все значимые изменения проекта документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
проект придерживается [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
и [Conventional Commits](https://www.conventionalcommits.org/ru/v1.0.0/).

Генерируется автоматически: `git-cliff -o CHANGELOG.md`.

Разделы: **Added** — новые возможности, **Changed** — изменения существующего,
**Fixed** — исправления, **Security** — улучшения безопасности.
## [unreleased]

### Added

- Add /exit command handler
- Add handlers for "назад" and "отменить" buttons
- Add gallery handler and update trial step text
- Add back step functionality and update trial flow
- Add web admin panel (port 5004), full README and templates
- Add logging, healthcheck, observability [Stage 5]

### Changed

- Этап 1 завершён: убран дубль content.py, все кнопки меню работают через teacher.json
- Этап 2 завершён: teacher.json наполнен реальным контентом Алексея Смирнова
- Этап 5 завершён: уведомления администратору работают
- Этап 6 завершён: бот запущен в Docker
- ✨ Универсальный шаблон: валидатор, 4 шаблона, скрипт инициализации
- Initial commit
- Update docker-compose version
- Adapt trial form for fitness trainer
- Externalize trial messages and enhance button matching
- Consolidate content page handlers, add DB error handling, and update commands
- Rename project from teacherbot to fitness-coach
- Split back and cancel handlers
- Convert bot to manicure master
- Rename goal to service
- Add .gitignore to protect tokens
- Fitness coach bot - fully functional
- Убран копипаст-остаток от психолог-бота: дублирующаяся галочка и сообщение о связи
- Update password information in README
- Update README to remove default password
- Add quality tools (ruff, pytest, pre-commit) [Stage 0]
- Auto-format by ruff (pre-commit)
- Auto-format tests (pre-commit)
- Add CI and quality-gates workflows, suppress bandit B104 with nosec
- Document CI/CD workflows and fix test commands in README
- Add acceptance report and quality docs; fix pytest pythonpath and bandit B104

### Fixed

- Handle missing 'parents' key
- Handle KeyError 'parents'
- Update success message
- Update success message
- Update success message
- Handle 'Cancel' and 'Back' buttons in trial flow
- Handle validation error
- Handle back button to return to previous step
- Clear user_data after successful form submission
- Добавлена валидация полей формы (возраст, контакт), убран дублирующий текст в success-сообщении

### Security

- Security hardening: fail-closed creds, rate-limit, html.escape, sanitize_cell, WAL+busy_timeout, cron backups, dockerignore/gitignore
- Security hardening Stage 1: hashed admin password (hmac/sha256), CSRF tokens, non-privileged appuser, backup script
