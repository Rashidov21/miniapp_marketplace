# UX yaxshilanishlari (qisqa)

## Maqsad

Telegram Mini App ichida **kam bosish**, **aniq yozuvlar**, **mobil bir qo‘l** bilan ishlash va **buyurtma konversiyasi** ustuvor.

## Asosiy o‘zgarishlar

1. **Xaridor**
   - Do‘kon: yuklanish paytida **skeleton**, mahsulotlar **karta** ko‘rinishida, narx va o‘tish aniq.
   - Mahsulot: **sticky bottom** — narx + “Buyurtma berish” doim pastda (CTA).
   - Buyurtma: **3 ta maydon**; ism **Telegramdan oldindan**; telefon **+998** normalizatsiyasi; **muvaffaqiyat ekrani** + do‘konga qaytish.
2. **Sotuvchi**
   - Kabinet: **onboarding** matni qisqa; **havola nusxalash**; buyurtmalar **karta** — telefon `tel:`, manzil alohida, holat **rang badge**, **“Qabul qildim” / “Yetkazildi”** tugmalari.
3. **Umumiy**
   - `MiniApp` yordamchilari: `getSuggestedName`, `normalizePhoneUz`, `escapeHtml`, **haptic** engil.
   - Xatoliklarni **JSON detail**dan chiqarish (DRF) xabari.

## Keyingi qadamlar (tavsiya)

- **Telegram MainButton** — buyurtma yuborish uchun rasmiy “Tayyor” tugmasi.
- **Rasm** uchun avtomatik siqish oldindan ko‘rinish (preview).
- **Buyurtma** uchun bir marta **qo‘ng‘iroq** tugmasi sotuvchiga (tel: link allaqachon).
- **ru** locale uchun `compilemessages` va til tanlash (keyin).
