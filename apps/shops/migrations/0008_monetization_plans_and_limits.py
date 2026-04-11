from decimal import Decimal

from django.db import migrations, models


def seed_monetization(apps, schema_editor):
    SubscriptionPlan = apps.get_model("shops", "SubscriptionPlan")
    SubscriptionPlan.objects.all().update(
        max_products=None,
        includes_advanced_analytics=True,
        is_active=False,
    )
    SubscriptionPlan.objects.create(
        name="50 mahsulotgacha",
        duration_months=1,
        price=Decimal("29000.00"),
        currency="UZS",
        is_active=True,
        sort_order=0,
        max_products=50,
        includes_advanced_analytics=False,
    )
    SubscriptionPlan.objects.create(
        name="Cheksiz + analytics",
        duration_months=1,
        price=Decimal("59000.00"),
        currency="UZS",
        is_active=True,
        sort_order=1,
        max_products=None,
        includes_advanced_analytics=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("shops", "0007_shop_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriptionplan",
            name="includes_advanced_analytics",
            field=models.BooleanField(
                default=False,
                help_text="Haftalik analytics va keyingi bosqichdagi hisobotlar.",
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="max_products",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Null — cheksiz mahsulot (Pro). Raqam — faol mahsulot limiti.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="shop",
            name="first_order_completed_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Birinchi muvaffaqiyatli buyurtma vaqti (upsell / CRO).",
                null=True,
            ),
        ),
        migrations.RunPython(seed_monetization, noop),
    ]
