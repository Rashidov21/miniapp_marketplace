# Mini App — UI ↔ API

Barcha `MiniApp.apiFetch` chaqiriqlari `/api` prefiksi bilan `static/js/app.js` orqali ketadi (CSV eksport bundan mustasno: to‘liq `/api/seller/orders/export/`).

## Bosh sahifa (`/webapp/`)

| Amal | Endpoint |
|------|----------|
| Auth | `POST /auth/telegram/` |
| Profil | `GET /me/` |
| Do‘kon bormi | `GET /shops/mine/` (200 → do‘kon bor; 404/403 → yo‘q) |
| Do‘kon bor | redirect `GET /webapp/seller/shop/` (egasi — do‘kon profili) |
| Sotuvchi/admin, do‘kon yo‘q | redirect `GET /webapp/seller/` (kabinet) |
| Mijoz, buyurtma bor | redirect `GET /webapp/my-orders/` (`GET /orders/mine/?page_size=1`) |
| Mijoz, buyurtma yo‘q | redirect `GET /webapp/discover/` |
| Katalog (ochiq do‘konlar) | `GET /shops/discover/` (sahifa: `/webapp/discover/`) |

## Do‘kon / mahsulot (ochiq)

| Sahifa | Endpoint |
|--------|----------|
| Katalog | `GET /shops/<id>/public/`, `GET /shops/<id>/products/` (+ `next` sahifalash) |
| Ulashish | `GET /shops/<id>/public/link/` |
| Mahsulot | `GET /shops/<id>/products/<id>/public/`, `.../public/link/` |

## Buyurtma (xaridor)

| Sahifa | Endpoint |
|--------|----------|
| Yaratish | `POST /orders/` |
| Ro‘yxat | `GET /orders/mine/` |
| Batafsil | `GET /orders/<id>/` |
| Bekor | `POST /orders/<id>/cancel/` |
| Izohlar | `GET/POST /orders/<id>/notes/` |

## Sotuvchi kabineti

| Sahifa | Endpoint |
|--------|----------|
| Auth, profil, do‘kon | `POST /auth/telegram/`, `GET /me/`, `GET /shops/mine/`, `POST /shops/`, `POST /me/become-seller/`, `POST /me/accept-seller-terms/` |
| Buyurtmalar | `GET /seller/orders/`, `POST .../accept/`, `/deliver/`, `/cancel/` |
| Izohlar | `GET/POST /orders/<id>/notes/` |
| CSV | `GET /api/seller/orders/export/` (`fetch` + headerlar) |
| Stat | `GET /seller/stats/` |
| Havola | `GET /shops/<id>/link/` |
| Mahsulotlar ro‘yxati | `GET /seller/products/` |
| Checklist | `GET /seller/products/?page_size=1` |

## Mahsulot formasi

| Amal | Endpoint |
|------|----------|
| Chek / limit | `GET /shops/mine/` |
| Olish / saqlash | `GET/PATCH/POST /seller/products/...` |

## Do‘kon sozlamalari

| Amal | Endpoint |
|------|----------|
| Yuklash / saqlash | `GET /shops/mine/`, `PATCH /shops/<id>/` |

## Obuna

| Amal | Endpoint |
|------|----------|
| Reja | `GET /subscription/plans/` |
| To‘lov | `POST /shops/mine/payments/` |

## Mini Appda ishlatilmaydi (mo‘ljallangan)

- `PATCH /seller/orders/<id>/` — umumiy holat o‘zgartirish; UI faqat `accept` / `deliver` / `cancel` POST laridan foydalanadi.
- `POST/PATCH /admin/products/<id>/` — platforma moderatsiyasi; alohida API.
- `GET /api/platform/stats/` — platform paneli.
