# Generated manually for buyer checkout UX (Click / payment instructions).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shops", "0009_subscription_tiers_25_50_unlimited"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="payment_note",
            field=models.TextField(
                blank=True,
                max_length=800,
                help_text="Mijozga: buyurtma va mahsulot sahifasida ko‘rinadi. Click havolasi, karta raqami yoki «naqd yetkazganda» kabi qisqa tartib (buyurtmadan platforma ulush olmaydi).",
            ),
        ),
    ]
