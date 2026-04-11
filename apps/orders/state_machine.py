"""Allowed order status transitions (single direction, production-safe)."""
from __future__ import annotations

from apps.orders.models import Order


def allowed_next_statuses(current: str) -> frozenset[str]:
    """Return valid target statuses from *current*."""
    s = Order.Status
    if current == s.NEW:
        return frozenset({s.ACCEPTED, s.CANCELLED})
    if current == s.ACCEPTED:
        return frozenset({s.DELIVERED})
    return frozenset()


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in allowed_next_statuses(from_status)
