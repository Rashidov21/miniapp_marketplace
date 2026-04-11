"""
Telegram /start dan keyin yuboriladigan kechikkan xabarlar — foydalanuvchi holatiga qarab.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from django.conf import settings

from apps.products.models import Product
from apps.shops.models import Shop
from apps.users.models import User

DelayMsg = Tuple[int, str]

# (soniya kutish, matn) — maks. 3 ta, umumiy vaqt ~2 daqiqadan oshmasin
DEFAULT_DELAYS = (8, 28, 72)


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
    if not telegram_user_id:
        return _seq(
            DEFAULT_DELAYS,
            "⏱ SavdoLink: 1 daqiqada do‘kon ochishingiz mumkin.\n«Mini Appni ochish» → Sotuvchi kabineti.",
            "📦 Mahsulot qo‘shing va bitta havolani ulashing — buyurtmalar chatda yo‘qolmaydi.",
            "✅ Tayyormisiz? Mini App → Sotuvchi kabineti — hozir sinab ko‘ring.",
        )

    user = User.objects.filter(telegram_id=telegram_user_id).first()
    if not user:
        return _seq(
            DEFAULT_DELAYS,
            "⏱ Birinchi marta: Mini App'ni oching — sotuvchi bo‘ling va do‘kon nomini yozing.",
            "📦 Keyin mahsulot qo‘shing — mijozlar katalogdan buyurtma beradi.",
            "🔗 Do‘kon havolasini Instagram yoki guruhga qo‘ying.",
        )

    shop = Shop.objects.filter(owner=user).first()
    if not shop:
        return _seq(
            DEFAULT_DELAYS,
            f"👋 {user.first_name or 'Siz'} — hali do‘kon yo‘q. Mini App → Sotuvchi kabineti → do‘kon yarating.",
            "✏️ Do‘kon nomi va tavsif — keyin mahsulot qo‘shish oson.",
            "⚡ 5 daqiqada vitrinangiz tayyor bo‘lishi mumkin.",
        )

    product_count = Product.objects.filter(shop=shop, is_active=True).count()
    shop_name = shop.name or "Do‘koningiz"

    if product_count == 0:
        return _seq(
            DEFAULT_DELAYS,
            f"📦 {shop_name}: do‘kon bor — endi kamida bitta mahsulot qo‘shing (narx + rasm).",
            "🖼️ Mahsulot rasmi va aniq narx — ko‘proq buyurtma.",
            "📎 Keyin «Mijoz havolasi»ni nusxalab ulashing.",
        )

    if not shop.is_active or not shop.is_subscription_operational():
        return _seq(
            DEFAULT_DELAYS,
            "⚠️ Do‘koningiz hozir mijozlarga yopiq yoki obuna muddati tugagan bo‘lishi mumkin.",
            "💳 Mini App → Obuna — tarifni yangilang yoki to‘lovni tekshiring.",
            "📩 Savol bo‘lsa, platforma orqali yozishingiz mumkin.",
        )

    if not shop.first_order_completed_at:
        return _seq(
            DEFAULT_DELAYS,
            f"✅ {shop_name}: mahsulotlar joyida. Endi havolani ulashing — birinchi buyurtmani kutamiz.",
            "📣 Instagram bio, story, Telegram guruh — bitta link.",
            "🔔 Yangi buyurtma kelganda shu yerga xabar boradi.",
        )

    # Barqaror sotuvchi
    return _seq(
        DEFAULT_DELAYS,
        f"🙌 {shop_name}: savdo davom etsin — yangi mahsulot yoki aksiya qo‘shing.",
        "📊 Ko‘proq tahlil va limit uchun Pro tarifni ko‘ring (Mini App → Obuna).",
        "⭐ Mijozlarga tez javob — qayta buyurtma ehtimoli oshadi.",
    )


def should_send_onboarding_nudges(chat_id: int) -> bool:
    """Kuniga cheklangan son marta nudge ketma-ketligi (spam oldini olish)."""
    from django.core.cache import cache

    max_per_day = int(getattr(settings, "BOT_ONBOARDING_MAX_PER_DAY", 6))
    key = f"bot_onboarding_day:{chat_id}"
    n = cache.get(key, 0)
    if n >= max_per_day:
        return False
    cache.set(key, n + 1, 86400)
    return True
