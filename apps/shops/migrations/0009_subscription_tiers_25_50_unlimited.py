"""Oylik tariflar: 25 / 50 / cheksiz (29k / 49k / 99k UZS)."""

from decimal import Decimal

from django.db import migrations


def seed_tiers(apps, schema_editor):
    SubscriptionPlan = apps.get_model("shops", "SubscriptionPlan")
    SubscriptionPlan.objects.filter(is_active=True).update(is_active=False)
    SubscriptionPlan.objects.create(
        name="25 tagacha",
        duration_months=1,
        price=Decimal("29000.00"),
        currency="UZS",
        is_active=True,
        sort_order=0,
        max_products=25,
        includes_advanced_analytics=False,
    )
    SubscriptionPlan.objects.create(
        name="50 tagacha",
        duration_months=1,
        price=Decimal("49000.00"),
        currency="UZS",
        is_active=True,
        sort_order=1,
        max_products=50,
        includes_advanced_analytics=False,
    )
    SubscriptionPlan.objects.create(
        name="Cheksiz + Pro analytics",
        duration_months=1,
        price=Decimal("99000.00"),
        currency="UZS",
        is_active=True,
        sort_order=2,
        max_products=None,
        includes_advanced_analytics=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shops", "0008_monetization_plans_and_limits"),
    ]

    operations = [
        migrations.RunPython(seed_tiers, noop),
    ]
