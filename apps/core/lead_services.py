"""Landing lead — Telegram xabarnoma."""
from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from apps.core.models import Lead
from apps.core.telegram import send_message


def _lead_source_uz(lead: Lead) -> str:
    m = {
        Lead.Source.LANDING_MODAL: "Landing (modal oyna)",
        Lead.Source.LANDING_STICKY: "Landing (pastki tugma)",
        Lead.Source.LANDING_HERO: "Landing (hero blok)",
        Lead.Source.LANDING_FINAL: "Landing (oxirgi CTA)",
    }
    return m.get(lead.source, lead.get_source_display())


def notify_lead_admins(lead: Lead) -> None:
    raw = (getattr(settings, "LANDING_NOTIFY_TELEGRAM_IDS", "") or "").strip()
    ids: list[int] = []
    for part in raw.split(","):
        p = part.strip()
        if p.isdigit():
            ids.append(int(p))
    if not ids:
        return
    dt = timezone.localtime(lead.created_at).strftime("%Y-%m-%d %H:%M")
    lines = [
        "📝 Yangi SavdoLink arizasi",
        f"Ism: {lead.name}",
        f"Telefon: {lead.phone}",
        f"Manba: {_lead_source_uz(lead)}",
    ]
    if lead.comment:
        lines.append(f"Izoh: {lead.comment}")
    lines.append(f"Vaqt: {dt}")
    text = "\n".join(lines)
    for cid in ids:
        send_message(cid, text)
