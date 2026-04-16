"""Telegram Bot API helpers."""
from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_TELEGRAM_MAX_RETRIES = 3
_TELEGRAM_BACKOFF_SEC = 0.6


def _post_bot_api(method: str, payload: dict[str, Any]) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set; skip send_message")
        return False
    url = f"https://api.telegram.org/bot{token}/{method}"
    last_err: BaseException | None = None
    for attempt in range(_TELEGRAM_MAX_RETRIES):
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.ok:
                return True
            logger.warning(
                "Telegram %s HTTP %s (attempt %s/%s): %s",
                method,
                r.status_code,
                attempt + 1,
                _TELEGRAM_MAX_RETRIES,
                r.text[:500],
            )
            if r.status_code in (429, 500, 502, 503, 504) and attempt + 1 < _TELEGRAM_MAX_RETRIES:
                time.sleep(_TELEGRAM_BACKOFF_SEC * (attempt + 1))
                continue
            return False
        except requests.RequestException as e:
            last_err = e
            logger.warning(
                "Telegram %s request error (attempt %s/%s): %s",
                method,
                attempt + 1,
                _TELEGRAM_MAX_RETRIES,
                e,
            )
            if attempt + 1 < _TELEGRAM_MAX_RETRIES:
                time.sleep(_TELEGRAM_BACKOFF_SEC * (attempt + 1))
    if last_err:
        logger.exception("Telegram %s failed after retries", method)
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
