"""DB-level locks for idempotency (PostgreSQL advisory locks)."""
from __future__ import annotations

import hashlib

from django.db import connection


def advisory_xact_lock_for_string(key: str) -> None:
    """
    Serialize transactions that share the same logical key (e.g. Idempotency-Key).
    No-op on non-PostgreSQL backends (small race window remains there).
    """
    if connection.vendor != "postgresql":
        return
    h = hashlib.sha256(key.encode()).digest()
    lock_id = int.from_bytes(h[:8], "big", signed=False) % (2**62)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
