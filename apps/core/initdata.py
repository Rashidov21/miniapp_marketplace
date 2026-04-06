"""Verify Telegram WebApp initData (hash) per Telegram documentation."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any
from urllib.parse import parse_qsl


def verify_init_data(init_data: str, bot_token: str) -> dict[str, Any] | None:
    """
    Returns parsed user payload if valid, else None.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not bot_token or not init_data:
        return None
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None
    data_check_parts = []
    for key in sorted(parsed.keys()):
        data_check_parts.append(f"{key}={parsed[key]}")
    data_check_string = "\n".join(data_check_parts)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()
    computed = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        return None
    user_raw = parsed.get("user")
    user: dict[str, Any] = {}
    if user_raw:
        try:
            user = json.loads(user_raw)
        except json.JSONDecodeError:
            return None
    return {
        "user": user,
        "auth_date": parsed.get("auth_date"),
        "query_id": parsed.get("query_id"),
        "start_param": parsed.get("start_param") or "",
    }
