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
4. Do‘kon havolasi: `https://t.me/<USERNAME>?startapp=shop_<ID>` (API: `GET /api/shops/<id>/link/`).

## API (qisqacha)

- `POST /api/auth/telegram/` — `{ "init_data": "<Telegram.WebApp.initData>" }`
- `GET /api/me/` — `X-Telegram-Init-Data` sarlavhasi bilan
- `POST /api/me/become-seller/` — sotuvchi roliga o‘tish
- `POST /api/shops/` — do‘kon yaratish
- `GET /api/shops/<id>/public/` — ochiq do‘kon
- `GET /api/shops/<id>/products/` — mahsulotlar ro‘yxati
- `POST /api/orders/` — buyurtma (autentifikatsiya talab qilinadi)

Barcha himoyalangan so‘rovlar: sarlavha `X-Telegram-Init-Data: <initData>`.

## Django admin

```bash
python manage.py createsuperuser
# telegram_id ni unikal raqam sifatida kiriting (masalan, o‘z Telegram ID)
```

Admin: `/admin/` — foydalanuvchilar, do‘konlar (`is_active`, `is_verified`), buyurtmalar.

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
