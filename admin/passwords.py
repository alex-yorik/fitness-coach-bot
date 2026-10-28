"""Хеширование пароля админки: PBKDF2-HMAC-SHA256.

Формат: pbkdf2_sha256:<iterations>:<salt_hex>:<hash_hex>
Почему без $: символ $ ломается при передаче через env_file в docker-compose.
"""

import getpass
import hashlib
import hmac
import secrets


def hash_password(password: str, iterations: int = 600_000) -> str:
    """Сгенерировать хеш пароля.

    Args:
        password: пароль в открытом виде
        iterations: число итераций PBKDF2 (по умолчанию 600 000)

    Returns:
        строка формата pbkdf2_sha256:<iterations>:<salt_hex>:<hash_hex>
    """
    salt = secrets.token_bytes(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256:{iterations}:{salt.hex()}:{pw_hash.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Проверить пароль против сохранённого хеша.

    Args:
        password: пароль в открытом виде
        stored: сохранённый хеш в формате pbkdf2_sha256:<iterations>:<salt_hex>:<hash_hex>

    Returns:
        True если пароль совпадает, False иначе (включая неверный формат)
    """
    try:
        prefix, iterations_str, salt_hex, hash_hex = stored.split(":")
    except (ValueError, AttributeError):
        return False

    if prefix != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
    except (ValueError, TypeError):
        return False

    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(pw_hash, expected_hash)


def main():
    """CLI: сгенерировать хеш пароля."""
    password = getpass.getpass("Введите пароль: ")
    password2 = getpass.getpass("Повторите пароль: ")

    if password != password2:
        print("Пароли не совпадают.", flush=True)
        return

    if not password:
        print("Пароль не может быть пустым.", flush=True)
        return

    h = hash_password(password)
    print(f"\nДобавьте в .env:\nFLASK_PASSWORD_HASH={h}", flush=True)


if __name__ == "__main__":
    main()
