# Telegram Bot Development Rules

## Environment:
- Docker container, Ubuntu 24.04
- Python 3.12, python-telegram-bot v20+
- Async/await pattern
- SQLite database at /app/data/database.db

## Project Structure:
- app/handlers/ - command handlers (trial.py, start.py, etc.)
- app/keyboards.py - inline and reply keyboards
- app/content_loader.py - load texts from JSON files
- app/database.py - database operations
- content/*.json - bot texts and configuration

## Code Change Format:
ALWAYS use SEARCH/REPLACE blocks:

SEARCH:
```python
old code here
```

REPLACE:
```python
new code here
```

## Coding Rules:

### ALWAYS:
Use SEARCH/REPLACE format for all changes
Check file exists before editing
Show exact line numbers
Keep changes minimal (max 20 lines per change)
One file at a time
Use type hints
Follow PEP 8
Test syntax with python3 -m py_compile file.py

### NEVER:
Invent non-existent commands or flags
Change working code without reason
Add unused imports
Create files without explicit request
Use interactive commands (vim, nano, less)
Guess file paths - use find to locate
Large refactoring without request
Change JSON structure without asking

## Error Handling:
1. Read error message carefully
2. DO NOT repeat failed command
3. Check error output
4. Suggest alternative solution
5. Use find to locate files if path unknown
6. Ask if unsure

## Docker Commands:
- Build: docker-compose build --no-cache
- Start: docker-compose up -d
- Logs: docker-compose logs -f --tail=30
- Restart: docker-compose restart
- Stop: docker-compose down

## Communication:
- Be concise and technical
- Show code changes clearly in SEARCH/REPLACE format
- Explain WHY not just WHAT
- Ask clarifying questions if requirements unclear
- Suggest best practices
