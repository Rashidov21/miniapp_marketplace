from __future__ import annotations

from typing import Any

from apps.platform.models import StaffAuditLog


def log_staff_action(
    actor,
    action: str,
    *,
    target_type: str = "",
    target_id: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    StaffAuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type or "",
        target_id=str(target_id) if target_id else "",
        payload=payload or {},
    )
