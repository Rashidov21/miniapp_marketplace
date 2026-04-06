# Production audit — Mini App marketplace

## 1. Executive summary

The MVP is **functionally solid** (Telegram initData, idempotent orders, subscription, platform panel).  
This document lists **findings**, **applied fixes** in code, and **recommended next steps** for Uzbekistan production traffic.

---

## 2. Architecture — strengths

| Area | Notes |
|------|--------|
| Django apps split | `users`, `shops`, `products`, `orders`, `core`, `platform` — clear boundaries |
| DRF + function views | Simple, debuggable; suitable for small team |
| PostgreSQL | Appropriate for relational + constraints |
| Static + Manifest (prod) | Cache-busting for JS/CSS |
| Idempotency + throttle | Orders protected from replay + abuse |

---

## 3. Issues found (and status)

### Backend

| Issue | Severity | Status |
|-------|----------|--------|
| Order status could jump arbitrarily (e.g. NEW → DELIVERED) | High | **Fixed** — `state_machine.py` |
| N+1 risk on some serializers | Medium | **Improved** — `select_related` on hot paths |
| Public product list unbounded | Medium | **Fixed** — pagination |
| Seller order list unbounded | Medium | **Fixed** — pagination |
| Missing DB indexes on `Order`/`Product` filters | Medium | **Fixed** — migrations |
| `OrderCreateSerializer` weak field validation | Medium | **Fixed** — length + `PrimaryKeyRelatedField` queryset |

### Security

| Issue | Status |
|-------|--------|
| initData auth_date + hash | Already enforced |
| Staff vs Telegram API | Platform uses session + role |
| CSRF on web forms | Django default |

### Frontend / UX

| Issue | Recommendation |
|-------|----------------|
| Tailwind CDN in prod | Build step or self-host Tailwind for CSP |
| Some pages lack empty/error copy | Gradual template pass |
| `shop.html` pagination | Client may ignore `next` — add “Load more” later |

### Admin (Django)

| Gap | Mitigation |
|-----|------------|
| Platform ops split between `/admin/` and `/platform/` | Document; use `/platform/` for payments |

---

## 4. Performance targets

- **API < 300 ms** — depends on server/network; indexes + `select_related` reduce DB time.
- **Images** — `Product.save` already compresses uploads (Pillow).
- **Pagination** — public products + seller orders paginated.

---

## 5. i18n

- Default `LANGUAGE_CODE = uz` — keep.
- All user-facing strings should use `{% trans %}` / `gettext_lazy`.
- **Russian** — add `django.po` entries and `?lang=ru` or user preference later.

---

## 6. Final recommendations

1. **Monitoring** — Sentry + Gunicorn access logs.
2. **Backups** — Postgres daily + media snapshot.
3. **Rate limits** — extend to more public endpoints if abused.
4. **Celery** — move Telegram sends off-thread to queue at scale.
5. **E2E tests** — order flow + subscription.

---

*Generated as part of the production readiness pass.*
