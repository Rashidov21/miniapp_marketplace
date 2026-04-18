# Kabinet segmentlari (amalga oshirilgan)

Maqsad: `/webapp/seller/` sahifasida foydalanuvchi **rol + do‘kon** bo‘yicha faqat kerakli bloklarni ko‘radi.

## Segmentlar

| Holat | Shart | Buyurtmalar bo‘limi | Mahsulot CTA | Qayd |
|-------|--------|---------------------|--------------|------|
| **Do‘kon bor** | `GET /shops/mine/` 200 | Ko‘rinadi, `loadOrders()` | Ko‘rinadi | `showShopDashboardUi` |
| **Sotuvchi/admin, do‘kon yo‘q** | `isPanelRole` va shop yo‘q | Yashirin, API chaqirilmaydi | Yashirin | Onboarding: do‘kon yaratish |
| **Xaridor, do‘kon yo‘q** | buyer va shop yo‘q | Yashirin | Yashirin | `#buyer-kabinet-hint` + onboarding; checklist yashirin |

## Boshqa qoidalar

- **CSV + holat filtri** (`#orders-toolbar`): faqat jami buyurtma soni > 0 yoki ro‘yxat bo‘sh emas bo‘lganda ko‘rinadi.
- **Server kontekst** (`seller_dashboard` view): `dashboard_role`, `dashboard_has_shop` — `data-*` atributlari (`#seller-dashboard-root`) uchun; asosiy mantiq JS + API.

## Tegishli fayllar

- `apps/core/views.py` — `seller_dashboard`
- `templates/webapp/seller_dashboard.html`
