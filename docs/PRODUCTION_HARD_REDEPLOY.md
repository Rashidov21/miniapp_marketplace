# Production: xavfsiz “hard redeploy” (Django + Gunicorn + Nginx + PostgreSQL)

Maqsad: **yangi UI/UX** bilan toza deploy, **static yangilanishi**, **kesh muammalari yo‘q**, **zero broken state**.

Quyidagi yo‘llarni o‘z VPS ga moslang:

| O‘zgaruvchi | Misol |
|-------------|--------|
| `PROJECT_DIR` | `/var/www/miniapp_marketplace` |
| `VENV` | `$PROJECT_DIR/venv` |
| `DB_NAME` | `.env` dagi `POSTGRES_DB` yoki `miniapp_marketplace` |
| `GUNICORN_SERVICE` | `gunicorn-miniapp` (yoki sizda qanday nomlangan bo‘lsa) |
| `BACKUP_DIR` | `/var/backups/miniapp` |

---

## STEP 1 — Pre-check

Loyihada (`config/settings.py`):

- `DEBUG` → `DJANGO_DEBUG` env orqali; productionda **`DJANGO_DEBUG=false`** (yoki o‘chirilgan).
- `ALLOWED_HOSTS` → **`DJANGO_ALLOWED_HOSTS`** — vergul bilan: `example.com,www.example.com,127.0.0.1`
- `SECRET_KEY` → **`DJANGO_SECRET_KEY`** — kuchli, tasodifiy, repoda yo‘q.
- DB → **`POSTGRES_DB`**, **`POSTGRES_USER`**, **`POSTGRES_PASSWORD`**, **`POSTGRES_HOST`**, **`POSTGRES_PORT`**

Serverda tekshirish (`.env` o‘qiladi):

```bash
cd /var/www/miniapp_marketplace   # PROJECT_DIR
set -a && source .env && set +a
echo "DEBUG must be false: DJANGO_DEBUG=$DJANGO_DEBUG"
echo "ALLOWED_HOSTS: $DJANGO_ALLOWED_HOSTS"
test -n "$DJANGO_SECRET_KEY" && echo "SECRET_KEY: set" || echo "SECRET_KEY: MISSING"
echo "DB: $POSTGRES_HOST:$POSTGRES_PORT / $POSTGRES_DB / user=$POSTGRES_USER"
```

Agar `USE_SQLITE=1` bo‘lsa, PostgreSQL o‘rniga SQLite ishlatiladi — backup strategiyani moslang.

---

## STEP 2 — Backup

```bash
sudo mkdir -p /var/backups/miniapp
TS=$(date +%Y%m%d_%H%M%S)
cd /var/www/miniapp_marketplace
set -a && source .env && set +a

# PostgreSQL (SQLite bo‘lsa: db.sqlite3 ni nusxalang)
sudo -u postgres pg_dump -Fc "$POSTGRES_DB" > "/var/backups/miniapp/db_${TS}.dump"

# Loyiha papkasi (venv va staticfiles ni istisno qilish mumkin — hajm kichrayadi)
sudo tar -czf "/var/backups/miniapp/project_${TS}.tar.gz" \
  -C /var/www miniapp_marketplace \
  --exclude='miniapp_marketplace/venv' \
  --exclude='miniapp_marketplace/staticfiles' \
  --exclude='miniapp_marketplace/**/__pycache__'
```

Restore (faqat zarurat bo‘lsa): `pg_restore -d DBNAME file.dump` yoki `psql`.

---

## STEP 3 — Yangi kod

```bash
cd /var/www/miniapp_marketplace
git fetch origin
git status
git pull origin main
```

Agar merge conflict bo‘lsa: hal qiling, keyin davom eting.

---

## STEP 4 — Install

```bash
cd /var/www/miniapp_marketplace
source venv/bin/activate
pip install -r requirements.txt
```

**Tailwind / CSS:** yangi UI `static/css/tailwind-built.css` da bo‘lishi kerak.

```bash
# Node bor bo‘lsa serverda:
npm ci
npm run build:css
```

Node yo‘q bo‘lsa: lokalda `npm run build:css` qilib `tailwind-built.css` ni commit qiling, keyin `git pull`.

---

## STEP 5 — Migratsiyalar

```bash
source venv/bin/activate
python manage.py migrate --noinput
```

Xatolik bo‘lsa: backupdan qaytish rejangiz bo‘lsin; `migrate` ni to‘xtatib, logni saqlang.

---

## STEP 6 — Static (`STATIC_ROOT` = `BASE_DIR/staticfiles`)

`DEBUG=False` da **ManifestStaticFilesStorage** — hashed fayllar; **har deploydan keyin** `collectstatic` majburiy.

```bash
source venv/bin/activate
python manage.py collectstatic --noinput
```

**Nginx:** `location /static/` → `alias` yoki `root` bilan **`STATIC_ROOT`** papkasiga (butun tree, jumladan `staticfiles.json` manifest).

---

## STEP 7 — Kesh va workerlar

- **LocMem cache** (`CACHES` default) — jarayon ichida; **Gunicorn restart** keshni yangilaydi.
- Agar keyinroq Redis/Memcached qo‘shilsa: `python manage.py shell -c "from django.core.cache import cache; cache.clear()"` qo‘shiladi.

```bash
# Gunicorn qayta ishga tushganda workerlar yangilanadi
sudo systemctl restart gunicorn-miniapp
```

---

## STEP 8 — Servislarni qayta ishga tushirish

```bash
sudo nginx -t && sudo systemctl reload nginx
# yoki konf o‘zgarganda:
# sudo systemctl restart nginx
sudo systemctl status gunicorn-miniapp --no-pager
```

Gunicorn allaqachon STEP 7 da restart qilingan bo‘lsa, takrorlash zarur emas (faqat nginx yangilansa kifoya).

---

## STEP 9 — Tekshiruv (brauzer + curl)

```bash
curl -sI https://YOUR_DOMAIN/ | head -5
curl -sI https://YOUR_DOMAIN/webapp/ | head -5
curl -sI https://YOUR_DOMAIN/static/css/tailwind-built.css | head -5
```

Qo‘lda:

- Bosh sahifa
- `/webapp/`
- Mahsulot sahifasi
- Buyurtma oqimi
- Sotuvchi dashboard

Brauzerda **Ctrl+F5** yoki inkognito — eski UI keshdan qolmasin. Telegram Mini App: ilovani yopib qayta oching.

---

## STEP 10 — Loglar

```bash
sudo journalctl -u gunicorn-miniapp -n 80 --no-pager
sudo tail -n 80 /var/log/nginx/error.log
sudo tail -n 80 /var/log/nginx/access.log
```

502: ko‘pincha **Nginx upstream port** ≠ **Gunicorn socket/port**. `proxy_pass` va gunicorn bind bir xil bo‘lsin.

---

## STEP 11 — UI yangilanmay qolsa (cache bust)

1. `.env` da **`STATIC_ASSET_VERSION`** ni oshiring (masalan `20260424`).
2. Gunicorn restart (context processor env ni qayta o‘qiydi).
3. `collectstatic` allaqachon hashed fayllar beradi — asosiy muammo odatda **eski HTML** yoki **brauzer/Telegram kesh**.

```bash
# .env da STATIC_ASSET_VERSION=...
sudo systemctl restart gunicorn-miniapp
```

---

## Tez-tez uchraydigan muammolar

| Muammo | Yechim |
|--------|--------|
| 502 Bad Gateway | Gunicorn ishlamayapti yoki noto‘g‘ri port/socket; `systemctl status`, Nginx `proxy_pass` |
| 404 `/static/...` | `collectstatic` qilinmagan yoki Nginx `alias` noto‘g‘ri `STATIC_ROOT` ga |
| Eski CSS/JS | `collectstatic`, keyin brauzer qattiq yangilash; `STATIC_ASSET_VERSION` bump |
| CSRF / ALLOWED_HOSTS | `DJANGO_ALLOWED_HOSTS` da domen va `www` |
| Migratsiya xatosi | Backupdan qaytish; `showmigrations`, log |

---

## Checklist (nusxa olish uchun)

- [ ] `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS` to‘liq
- [ ] `DJANGO_SECRET_KEY` va DB parollari o‘rnatilgan
- [ ] `pg_dump` + loyiha arxivi
- [ ] `git pull` muvaffaqiyatli
- [ ] `pip install -r requirements.txt`
- [ ] `npm run build:css` (yoki yangi CSS repoda)
- [ ] `migrate`
- [ ] `collectstatic --noinput`
- [ ] `nginx -t` + reload/restart
- [ ] `gunicorn` restart
- [ ] Sahifalar va API tekshiruvi
- [ ] Loglarda xato yo‘q
- [ ] Kerak bo‘lsa `STATIC_ASSET_VERSION` oshirildi

Bu tartib **xavfsiz redeploy** uchun standart; har safar backup qilish tavsiya etiladi.
