"""
Telegram /start dan keyin yuboriladigan kechikkan xabarlar — foydalanuvchi holatiga qarab.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.products.models import Product
from apps.shops.models import Shop
from apps.users.models import BotOnboardingQuota, User

DelayMsg = Tuple[int, str]

# Standart: birinchi eslatma ~5 daqiqadan keyin, keyingilari sozlamada (spam hissi bermaslik uchun).
_DEFAULT_DELAY_STR = "300,1800,14400"


def get_onboarding_delays() -> Tuple[int, int, int]:
    raw = (getattr(settings, "BOT_ONBOARDING_DELAYS", None) or _DEFAULT_DELAY_STR).strip()
    parts = [int(x.strip()) for x in raw.split(",") if x.strip()]
    if len(parts) != 3 or any(p < 0 for p in parts):
        return (300, 1800, 14400)
    return (parts[0], parts[1], parts[2])


def build_start_keyboard_markup(webapp_url: str, seller_url: str) -> dict:
    """inline (default) yoki reply — env: BOT_START_KEYBOARD_STYLE=inline|reply"""
    t1 = getattr(settings, "BOT_START_BUTTON_MINI_TEXT", None) or "Mini Appni ochish"
    t2 = getattr(settings, "BOT_START_BUTTON_SELLER_TEXT", None) or "Sotuvchi kabineti"
    style = (getattr(settings, "BOT_START_KEYBOARD_STYLE", "inline") or "inline").strip().lower()
    if style == "reply":
        return {
            "keyboard": [
                [{"text": t1, "web_app": {"url": webapp_url}}],
                [{"text": t2, "web_app": {"url": seller_url}}],
            ],
            "resize_keyboard": True,
            "is_persistent": True,
        }
    return {
        "inline_keyboard": [
            [{"text": t1, "web_app": {"url": webapp_url}}],
            [{"text": t2, "web_app": {"url": seller_url}}],
        ]
    }


def start_welcome_text(start_param: str) -> str:
    """`/start` parametri bo‘yicha birinchi xabar."""
    p = (start_param or "").strip().lower()
    base = (
        "SavdoLink — Telegramda 1 link bilan savdo boshlang.\n"
        "Quyidagi tugma orqali Mini App'ni oching: do‘kon yarating, mahsulot qo‘shing, buyurtmalarni tartibda oling."
    )
    if p == "landing":
        return (
            "Assalomu alaykum!\n\n"
            "Landing sahifasidan keldingiz — yaxshi tanlov.\n\n" + base
        )
    if p == "lead":
        return (
            "Assalomu alaykum!\n\n"
            "Arizangiz uchun rahmat! Endi bot orqali Mini App'ni ochib, bir necha daqiqada do‘konni boshlashingiz mumkin.\n\n"
            + base
        )
    if p.startswith("shop_") or p.startswith("product_"):
        return (
            "Assalomu alaykum!\n\n"
            "Havola orqali kirdingiz — katalogni ko‘rishingiz yoki o‘z do‘koningizni boshqarishingiz mumkin.\n\n"
            + base
        )
    return "Assalomu alaykum!\n\n" + base


def _seq(delays: Tuple[int, int, int], a: str, b: str, c: str) -> List[DelayMsg]:
    return [(delays[0], a), (delays[1], b), (delays[2], c)]


def build_onboarding_nudges(telegram_user_id: Optional[int], start_param: str) -> List[DelayMsg]:
    """
    Kechikkan xabarlar ketma-ketligi.
    DB da foydalanuvchi yo‘q (Mini App hech ochilmagan) — umumiy yo‘l-yo‘riq.
    """
    _ = start_param  # kelajakda segment bo‘yicha matn farqlash uchun
    delays = get_onboarding_delays()
    if not telegram_user_id:
        return _seq(
            delays,
            "⏱ SavdoLink: 1 daqiqada do‘kon ochishingiz mumkin.\n«Mini Appni ochish» → Sotuvchi kabineti.",
            "📦 Mahsulot qo‘shing va bitta havolani ulashing — buyurtmalar chatda yo‘qolmaydi.",
            "✅ Tayyormisiz? Mini App → Sotuvchi kabineti — hozir sinab ko‘ring.",
        )

    user = User.objects.filter(telegram_id=telegram_user_id).first()
    if not user:
        return _seq(
            delays,
            "⏱ Birinchi marta: Mini App'ni oching — sotuvchi bo‘ling va do‘kon nomini yozing.",
            "📦 Keyin mahsulot qo‘shing — mijozlar katalogdan buyurtma beradi.",
            "🔗 Do‘kon havolasini Instagram yoki guruhga qo‘ying.",
        )

    shop = Shop.objects.filter(owner=user).first()
    if not shop:
        return _seq(
            delays,
            f"👋 {user.first_name or 'Siz'} — hali do‘kon yo‘q. Mini App → Sotuvchi kabineti → do‘kon yarating.",
            "✏️ Do‘kon nomi va tavsif — keyin mahsulot qo‘shish oson.",
            "⚡ 5 daqiqada vitrinangiz tayyor bo‘lishi mumkin.",
        )

    product_count = Product.objects.filter(shop=shop, is_active=True).count()
    shop_name = shop.name or "Do‘koningiz"

    if product_count == 0:
        return _seq(
            delays,
            f"📦 {shop_name}: do‘kon bor — endi kamida bitta mahsulot qo‘shing (narx + rasm).",
            "🖼️ Mahsulot rasmi va aniq narx — ko‘proq buyurtma.",
            "📎 Keyin «Mijoz havolasi»ni nusxalab ulashing.",
        )

    if not shop.is_active or not shop.is_subscription_operational():
        return _seq(
            delays,
            "⚠️ Do‘koningiz hozir mijozlarga yopiq yoki obuna muddati tugagan bo‘lishi mumkin.",
            "💳 Mini App → Obuna — tarifni yangilang yoki to‘lovni tekshiring.",
            "📩 Savol bo‘lsa, platforma orqali yozishingiz mumkin.",
        )

    if not shop.first_order_completed_at:
        return _seq(
            delays,
            f"✅ {shop_name}: mahsulotlar joyida. Endi havolani ulashing — birinchi buyurtmani kutamiz.",
            "📣 Instagram bio, story, Telegram guruh — bitta link.",
            "🔔 Yangi buyurtma kelganda shu yerga xabar boradi.",
        )

    # Barqaror sotuvchi
    return _seq(
        delays,
        f"🙌 {shop_name}: savdo davom etsin — yangi mahsulot yoki aksiya qo‘shing.",
        "📊 Ko‘proq tahlil va limit uchun Pro tarifni ko‘ring (Mini App → Obuna).",
        "⭐ Mijozlarga tez javob — qayta buyurtma ehtimoli oshadi.",
    )


def should_send_onboarding_nudges(chat_id: int) -> bool:
    """Kuniga cheklangan son marta nudge ketma-ketligi (barcha Gunicorn workerlar uchun DB orqali)."""
    max_per_day = int(getattr(settings, "BOT_ONBOARDING_MAX_PER_DAY", 6))
    today = timezone.now().date()
    for _ in range(5):
        try:
            with transaction.atomic():
                obj, _ = BotOnboardingQuota.objects.select_for_update().get_or_create(
                    chat_id=chat_id,
                    day=today,
                    defaults={"count": 0},
                )
                if obj.count >= max_per_day:
                    return False
                BotOnboardingQuota.objects.filter(pk=obj.pk).update(count=F("count") + 1)
            return True
        except IntegrityError:
            continue
    return False
