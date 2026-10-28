"""Тесты для admin/passwords.py."""

from admin.passwords import hash_password, verify_password


def test_hash_verify_roundtrip():
    """Круговой тест: hash → verify."""
    h = hash_password("test123", iterations=1000)
    assert verify_password("test123", h) is True


def test_verify_wrong_password():
    """Неверный пароль → False."""
    h = hash_password("test123", iterations=1000)
    assert verify_password("wrong", h) is False


def test_verify_corrupted_hash():
    """Повреждённый хеш → False."""
    h = hash_password("test123", iterations=1000)
    corrupted = h[:-5] + "00000"
    assert verify_password("test123", corrupted) is False


def test_verify_empty_hash():
    """Пустой хеш → False."""
    assert verify_password("test123", "") is False


def test_verify_old_hmac_format():
    """Старый HMAC-формат → False."""
    assert verify_password("test123", "hmac_sha256:abc123") is False


def test_two_generations_different_hashes():
    """Две генерации одного пароля дают разные хеши (разная соль)."""
    h1 = hash_password("test123", iterations=1000)
    h2 = hash_password("test123", iterations=1000)
    assert h1 != h2
    # Но оба должны верифицироваться
    assert verify_password("test123", h1) is True
    assert verify_password("test123", h2) is True


def test_verify_none_hash():
    """None хеш → False."""
    assert verify_password("test123", None) is False
