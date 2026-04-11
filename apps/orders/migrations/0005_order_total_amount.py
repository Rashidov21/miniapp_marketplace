from decimal import Decimal

from django.db import migrations, models


def backfill_order_totals(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for o in Order.objects.select_related("product").iterator():
        try:
            price = o.product.price
        except Exception:
            price = Decimal("0")
        Order.objects.filter(pk=o.pk).update(total_amount=price)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_add_performance_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="total_amount",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Snapshot of line total at order time (product price × qty).",
                max_digits=12,
            ),
        ),
        migrations.RunPython(backfill_order_totals, noop),
    ]
