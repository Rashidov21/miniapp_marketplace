from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0004_product_cro_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="sort_order",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Lower numbers appear first in the catalog (0 = default).",
            ),
        ),
    ]
