from django.db import migrations
from decimal import Decimal


def seed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("shops", "SubscriptionPlan")
    if SubscriptionPlan.objects.exists():
        return
    plans = [
        ("3 oy", 3, Decimal("99000")),
        ("6 oy", 6, Decimal("179000")),
        ("12 oy", 12, Decimal("319000")),
    ]
    for i, (name, months, price) in enumerate(plans):
        SubscriptionPlan.objects.create(
            name=name,
            duration_months=months,
            price=price,
            currency="UZS",
            is_active=True,
            sort_order=i,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shops", "0004_shop_profile_subscription"),
    ]

    operations = [
        migrations.RunPython(seed_plans, noop),
    ]
