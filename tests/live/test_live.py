import os

import pytest

pytestmark = pytest.mark.live

_RUN_LIVE = os.getenv("RUN_LIVE_TESTS", "").lower() in ("1", "true", "yes")
_BOT_TOKEN = os.getenv("BOT_TOKEN")


@pytest.mark.skipif(
    not (_RUN_LIVE and _BOT_TOKEN),
    reason="Live Telegram tests require BOT_TOKEN and RUN_LIVE_TESTS=1",
)
async def test_bot_me_live():
    """Smoke-тест реального Telegram API (только для live-прогона)."""
    import telegram

    bot = telegram.Bot(_BOT_TOKEN)
    me = await bot.get_me()
    assert me.username
