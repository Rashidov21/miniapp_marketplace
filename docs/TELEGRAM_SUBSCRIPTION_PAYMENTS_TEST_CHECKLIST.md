# Telegram obuna to‘lovi — qo‘lda test rejasi

`TELEGRAM_BOT_TOKEN`, `TELEGRAM_PAYMENT_PROVIDER_TOKEN` (BotFather test yoki real provayder), webhook `telegram_webhook` ochiq bo‘lishi kerak.

## Muvaffaqiyatli to‘lov

1. Mini App → Obuna → tarif → **Telegram orqali to‘lash**.
2. `openInvoice` ochiladi, test kartasi / provayder rejimi bilan to‘lang.
3. `pre_checkout_query` → backend `answerPreCheckoutQuery(ok=True)`.
4. `successful_payment` kelgach: `SubscriptionPayment` **approved**, `telegram_payment_charge_id` to‘ldirilgan, `approve_subscription_payment` — do‘kon obunasi yangilangan.
5. Platforma **To‘lovlar**: kanal **Telegram invoice**, holat **Tasdiqlangan**; operator **Tasdiqlash** tugmasi shart emas (avtomatik).

## Rad etishlar

- **Noto‘g‘ri summa**: invoice summasini buzib bo‘lmasa, boshqa scenariy — boshqa foydalanuvchi hisobidan to‘lash: `pre_checkout` `from.id` ≠ do‘kon egasi `telegram_id` → rad.
- **Muddati o‘tgan / noto‘g‘ri payload**: noto‘g‘ri `invoice_payload` → rad.

## Idempotency

- Bir xil `successful_payment` / `telegram_payment_charge_id` ikki marta yuborilsa: ikkinchi marta **no-op** (ikki marta obuna uzaytirilmasin).

## Bitta `pending` cheklovi

- Do‘konda allaqachon `pending` to‘lov bo‘lsa: ikkinchi **Telegram invoice** yoki **skrinshot** yuborish → **409** (`payment_pending_exists`).
- Avvalgi `pending`ni rad / tasdiqlagach yangi invoice mumkin.

## UI

- **Skrinshot bilan yuborish** — form ochiladi, avvalgidek POST `/shops/mine/payments/`.
- `TELEGRAM_PAYMENT_PROVIDER_TOKEN` bo‘sh bo‘lsa: invoice endpoint **503** va tushunarli xabar.

## Platforma

- Filtr: **Skrinshot** / **Telegram invoice** + qidiruvda `invoice_payload` / `telegram_payment_charge_id` ishtiro etishi.
