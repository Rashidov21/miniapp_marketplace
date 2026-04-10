"""Consistent JSON error bodies for DRF: ``{"detail": str, "code"?: str}``."""
from __future__ import annotations

from rest_framework.response import Response


def error_response(detail: str, *, status: int = 400, code: str | None = None, extra: dict | None = None) -> Response:
    body: dict = {"detail": str(detail)}
    if code:
        body["code"] = code
    if extra:
        body.update(extra)
    return Response(body, status=status)
