"""Telegram Bot API helpers."""
from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _post_bot_api(method: str, payload: dict[str, Any]) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set; skip send_message")
        return False
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        r = requests.post(url, json=payload, timeout=15)
        if not r.ok:
            logger.error("Telegram %s failed: %s %s", method, r.status_code, r.text)
            return False
        return True
    except requests.RequestException as e:
        logger.exception("Telegram %s error: %s", method, e)
        return False


def send_message(chat_id: int | str, text: str, parse_mode: str | None = None) -> bool:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return _post_bot_api("sendMessage", payload)


def send_message_with_markup(
    chat_id: int | str,
    text: str,
    *,
    reply_markup: dict[str, Any],
    parse_mode: str | None = None,
) -> bool:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": reply_markup,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return _post_bot_api("sendMessage", payload)
