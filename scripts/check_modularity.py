#!/usr/bin/env python3
"""Gate: файл <= 500 строк, функция <= 50 строк (проверка на AST)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

MAX_FILE_LINES = 500
MAX_FUNC_LINES = 50

SKIP_DIRS = {
    ".git",
    ".opencode",
    ".aider",
    "backups",
    "logs",
    "data",
    "media",
    "templates",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


def iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def check_file_lines(path: Path) -> tuple[int, int] | None:
    count = sum(1 for _ in path.open(encoding="utf-8"))
    return (count, MAX_FILE_LINES) if count > MAX_FILE_LINES else None


def check_func_lines(path: Path) -> list[tuple[int, str, int, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[tuple[int, str, int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        size = node.end_lineno - node.lineno + 1
        if size > MAX_FUNC_LINES:
            violations.append((node.lineno, node.name, size, MAX_FUNC_LINES))
    return violations


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    files = iter_python_files(root)
    if not files:
        print("check_modularity: не найдено python-файлов")
        return 0

    errors: list[str] = []
    for path in files:
        over = check_file_lines(path)
        if over is not None:
            errors.append(f"{path.relative_to(root)}: {over[0]} строк (лимит {over[1]})")
        for lineno, name, size, limit in check_func_lines(path):
            errors.append(
                f"{path.relative_to(root)}:{lineno}: функция {name!r} — "
                f"{size} строк (лимит {limit})"
            )

    if errors:
        print("Модульность нарушена:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Модульность в порядке: проверено {len(files)} файлов")
    return 0


if __name__ == "__main__":
    sys.exit(main())
