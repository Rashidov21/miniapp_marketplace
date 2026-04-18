# VPS: to‘liq qayta ishga tushirish (Mini App — yangi UI + backend)

**To‘liq “safe hard redeploy” (backup, pre-check, checklist):** [PRODUCTION_HARD_REDEPLOY.md](./PRODUCTION_HARD_REDEPLOY.md)

Kodda `MiniApp.apiFetch` barcha so‘rovlarni `/api/...` orqali yuboradi; `templates/webapp` havolalari `/webapp/...` bilan mos. Agar serverda **eski UI** yoki **tugmalar ishlamayapti** ko‘rinsa, odatda sabab: **eskicha static fayllar**, **kesh**, **yangilanmagan kod** yoki **502 / API ulanmay qolish**.

## 1. Kodni yangilash

```bash
cd /var/www/miniapp_marketplace   # o‘z yo‘lingiz
git pull origin main
```

## 2. Tailwind CSS qayta yig‘ish (majburiy — yangi UI `tailwind-built.css` da)

Loyihada Node bor bo‘lsa:

```bash
npm ci
npm run build:css
```

Node bo‘lmasa: lokal mashinada `npm run build:css` qilib `static/css/tailwind-built.css` ni commit qiling va serverda `git pull`.

## 3. Python muhit va migratsiya

```bash
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

## 4. Static: `collectstatic` (production)

`DEBUG=False` bo‘lsa `ManifestStaticFilesStorage` ishlatiladi — **har deploydan keyin**:

```bash
python manage.py collectstatic --noinput
```

## 4.1 Bot: `/start` tugmalari va eslatmalar (`.env`)

| O‘zgaruvchi | Tavsif |
|-------------|--------|
| `BOT_ONBOARDING_DELAYS` | Uchta eslatma orasidagi soniyalar, vergul bilan. Default: `300,1800,14400` (~5 min, 30 min, 4 soat). |
| `BOT_ONBOARDING_MAX_PER_DAY` | Bir chat uchun kuniga necha marta ketma-ketlik (default `6`). |
| `BOT_START_BUTTON_MINI_TEXT` | Birinchi tugma matni (bo‘sh bo‘lsa — «Mini Appni ochish»). |
| `BOT_START_BUTTON_SELLER_TEXT` | Ikkinchi tugma matni (bo‘sh bo‘lsa — «Sotuvchi kabineti»). |
| `BOT_START_KEYBOARD_STYLE` | `inline` (default) yoki `reply` — pastki klaviatura bilan doimiy tugmalar. |

Deploydan keyin migratsiya: `users` ilovasidagi `TelegramWebhookDedup` / `BotOnboardingQuota` jadvallari.

## 5. Keshni yangilash (brauzer `app.js` / CSS ni eski versiyadan olmasin)

`.env` da (yoki tizim o‘zgaruvchisi):

```env
STATIC_ASSET_VERSION=20260422
```

(`config/settings.py` dagi default bilan moslang yoki yangi raqam qo‘ying.) Keyin Gunicorn qayta ishga tushadi — `base.html` dagi `?v={{ STATIC_ASSET_VERSION }}` yangilanadi.

## 6. Gunicorn (yoki boshqa WSGI)

```bash
sudo systemctl restart gunicorn-miniapp
sudo systemctl status gunicorn-miniapp
```

## 7. Nginx

- `proxy_pass` **Gunicorn porti** bilan bir xil (masalan `127.0.0.1:8000`).
- `/static/` va `/media/` `STATIC_ROOT` / `MEDIA_ROOT` ga yo‘naltirilgan bo‘lsin.
- Konf o‘zgarganda: `sudo nginx -t && sudo systemctl reload nginx`.

## 8. Tekshiruv

- `curl -I https://sizning-domen.uz/webapp/` — 200/302, 502 emas.
- Brauzerda **qattiq yangilash** (Ctrl+F5) yoki inkognito — eski UI keshdan qolmasin.
- Telegram Mini App: ilovani to‘liq yoping va qayta oching.

## 9. API va tugmalar

- Barcha API: `GET/POST https://domen/api/...` (sayt ildizida `/api/`).
- Agar faqat `/webapp/` ochilsa, lekin `/api/` boshqa joyga yoki bloklansa — `apiFetch` ishlamaydi. Nginxda **bir xil server**da `/api/` ham proxy qilinishi kerak.

## 10. Xavfsizlik

- `.env`, `DJANGO_SECRET_KEY`, database parollarni repoga qo‘shmang.
