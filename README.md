# Miniapp marketplace (Telegram Mini App)

Telegram ichidagi oddiy mini-do‘kon platformasi: sotuvchi mahsulot qo‘shadi, xaridor 1–2 bosishda buyurtma beradi. MVP: to‘lov integratsiyasi va savat yo‘q.

## Texnologiyalar

- **Backend:** Django 5, Django REST Framework, PostgreSQL
- **Frontend:** Django templates, Tailwind CSS (CDN), oddiy JavaScript
- **Autentifikatsiya:** Telegram WebApp `initData` (HMAC tekshiruvi)
- **Ishlab chiqish:** Docker Compose
- **Produksiya:** Gunicorn + Nginx

## Tezkor ishga tushirish (SQLite, lokal)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # Linux/macOS

pip install -r requirements.txt
copy .env.example .env          # kerak bo‘lsa, TELEGRAM_BOT_TOKEN qo‘ying
set USE_SQLITE=true             # PowerShell: $env:USE_SQLITE="true"
python manage.py migrate
python manage.py load_sample_data
python manage.py runserver
```

Brauzer: `http://127.0.0.1:8000/webapp/` — to‘liq ishlashi uchun Telegram Mini App ichida oching (initData kerak).

## Docker (PostgreSQL)

```bash
copy .env.example .env
# .env ichida DJANGO_SECRET_KEY, TELEGRAM_BOT_TOKEN, PUBLIC_BASE_URL va boshqalar

docker compose build
docker compose up
```

Ilova: `http://localhost:8000`. Ma’lumotlar bazasi: `postgres:16`, media fayllar volume’da saqlanadi.

## Telegram bot

1. [@BotFather](https://t.me/BotFather) orqali bot yarating, token oling.
2. Mini App URL ni HTTPS domeningizga qo‘ying (masalan: `https://your-domain.example/webapp/`).
3. `.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` (faqat username, @siz).
4. Do‘kon havolasi: `https://t.me/<USERNAME>?startapp=shop_<ID>` — ochilganda brauzer manzili `https://…/webapp/s/<slug>/` ko‘rinishida bo‘ladi (API: `GET /api/shops/<id>/link/`).
5. `/start` uchun webhook (faqat **inline** Web App tugmalari — barcha mijozlar uchun barqaror ochiladi):
   - `.env`: `TELEGRAM_WEBHOOK_SECRET=<uzun-maxfiy-string>`
   - Endpoint: `POST /api/bot/webhook/<TELEGRAM_WEBHOOK_SECRET>/`
   - Webhook o‘rnatish:
     `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-domain.example/api/bot/webhook/<TELEGRAM_WEBHOOK_SECRET>/`

## API (qisqacha)

- `POST /api/auth/telegram/` — `{ "init_data": "<Telegram.WebApp.initData>" }`
- `GET /api/me/` — `X-Telegram-Init-Data` sarlavhasi bilan
- `POST /api/me/become-seller/` — sotuvchi roliga o‘tish (oldingi `POST /api/me/accept-seller-terms/`)
- `POST /api/me/accept-seller-terms/` — joriy sotuvchi/marketplace shartlari versiyasini qabul qilish
- `POST /api/shops/` — do‘kon yaratish
- `GET /api/orders/mine/` — mijozning buyurtmalari (pagination)
- `GET /api/orders/<id>/` — bitta buyurtma (mijoz yoki admin)
- `POST /api/orders/<id>/cancel/` — mijoz: faqat **NEW** holatda bekor qilish (`CANCELLED`)
- Mini App: `/webapp/my-orders/<id>/` — buyurtma detali va bekor qilish
- `GET /api/seller/stats/` — sotuvchi: 7 kunlik ko‘rishlar, buyurtmalar, mahsulotlar soni
- `GET /api/shops/<id>/public/` — ochiq do‘kon
- `GET /api/shops/<id>/products/` — mahsulotlar ro‘yxati (ixtiyoriy `?q=` qidiruv)
- `POST /api/orders/` — buyurtma (autentifikatsiya talab qilinadi)

Barcha himoyalangan so‘rovlar: sarlavha `X-Telegram-Init-Data: <initData>`.

## Django admin va platform paneli

Bitta `User` modeli: login **maydoni — `telegram_id`**, parol: `python manage.py changepassword <telegram_id>`.

### `/admin/` (Django Admin)

```bash
python manage.py createsuperuser
# telegram_id — unikal raqam (masalan, o‘z Telegram ID)
```

`createsuperuser` odatda **`is_staff`**, **`is_superuser`**, **`role=admin`** beradi — `/admin/` va `/platform/` ikkalasiga ham kirish mumkin (parol bilan).

- **`/admin/`** ochilishi uchun odatda **`is_staff=True`** yoki **`is_superuser=True`** kerak.
- Agar foydalanuvchida faqat **`role=admin`** bo‘lib, **`is_staff=False`** qolgan bo‘lsa, **platform panel** ochilishi mumkin, lekin **klassik Django Admin** — yo‘q: admin orqali `is_staff` ni yoqing yoki `createsuperuser` dan foydalaning.

### `/platform/` (boshqaruv paneli)

- Kirish: **`telegram_id` + parol** (`/platform/login/`).
- Ruxsat: **`is_superuser`** yoki **`role`** = `admin` yoki `platform_owner` (`is_platform_staff`).
- Bu **`/admin/`** dan mustaqil: masalan operator **`is_staff` siz** ham platform orqali to‘lovlarni tasdiqlashi mumkin (agar roli va paroli mos bo‘lsa).

Qisqacha: **to‘liq operator** — `createsuperuser` + parol; **faqat platform** — `role` + parol, kerak bo‘lsa `is_staff` siz.

## Ko‘p tillilik

- Standart til: **o‘zbek** (`LANGUAGE_CODE = uz`, `Asia/Tashkent`).
- Rus tili uchun tayyor struktura: `locale/ru/LC_MESSAGES/django.po`.
- Tarjimalarni qo‘llash: `django-admin compilemessages`

## Namuna ma’lumotlar

```bash
python manage.py load_sample_data
```

## VPS (Gunicorn + Nginx)

1. Serverda Python 3.12+, PostgreSQL, Nginx o‘rnating.
2. Loyihani klonlang, virtual muhit, `pip install -r requirements.txt`.
3. `.env` ni produksiya qiymatlari bilan to‘ldiring (`DJANGO_DEBUG=false`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, HTTPS cookie sozlamalari).
4. `python manage.py migrate`, `python manage.py collectstatic`, media katalogiga yozish huquqi.
5. Gunicorn (namuna): `deploy/gunicorn.conf.py` bilan `config.wsgi:application`.
6. Nginx: `deploy/nginx.conf` ni domen va SSL ga moslang; static va media ni fayl tizimidan bering.

## Huquqiy sahifalar (WebApp)

- `/webapp/legal/terms/`, `/webapp/legal/privacy/`, `/webapp/legal/seller/`, `/webapp/legal/content/` — namunaviy matnlar; ishga tushirishdan oldin yuridik tekshiruv.
- `.env`: `CURRENT_SELLER_TERMS_VERSION` (masalan `1`) — yangilanganda sotuvchilar qayta rozilik berishi kerak.

## Statik fayl keshi

- `DEBUG=false` da `ManifestStaticFilesStorage` ishlatiladi.
- Agar Nginx oddiy `app.js` ni eski versiyada bersa: `STATIC_ASSET_VERSION` ni `.env` da o‘zgartiring yoki `collectstatic` + Gunicorn qayta yuklash.

## Monitoring (tavsiya)

- Gunicorn access/error loglarini aylantirish; `DisallowedHost` va 5xx uchun signal.
- Ixtiyoriy: Sentry (`sentry-sdk` + DSN), PostgreSQL backup, disk va `media/` hajmi.
- `ALLOWED_HOSTS`, `DJANGO_ALLOWED_HOSTS` va `SECURE_PROXY_SSL_HEADER` (Nginx orqali HTTPS) tekshirilsin.

## Xavfsizlik

- `initData` serverda HMAC bilan tekshiriladi (`apps/core/initdata.py`).
- Produksiyada `DJANGO_SECRET_KEY`, HTTPS, `SESSION_COOKIE_SECURE` / `CSRF_TRUSTED_ORIGINS` ni to‘g‘ri sozlang.

## Loyiha tuzilmasi

```
apps/
  core/       # initData, Telegram xabarlari
  users/      # User, Telegram auth
  shops/      # Shop
  products/   # Product
  orders/     # Order
templates/webapp/
static/js/
deploy/
```

## Litsenziya

Loyiha shartlarini o‘zingiz belgilang.
