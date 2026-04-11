from django.db import migrations, models
from django.utils.text import slugify


def fill_shop_slugs(apps, schema_editor):
    Shop = apps.get_model("shops", "Shop")
    for shop in Shop.objects.all():
        base = slugify(shop.name or "")[:60].strip("-") or "do-kon"
        slug = base
        n = 0
        while Shop.objects.exclude(pk=shop.pk).filter(slug=slug).exists():
            n += 1
            suffix = f"-{n}"
            slug = (base[: max(1, 60 - len(suffix))] + suffix).strip("-")
        shop.slug = slug
        shop.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("shops", "0006_subscriptionpayment_pending_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="slug",
            field=models.SlugField(
                blank=True,
                db_index=True,
                help_text="URL va havolalarda ko‘rinadi (lotin harflar, raqam, tire).",
                max_length=80,
                null=True,
            ),
        ),
        migrations.RunPython(fill_shop_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="shop",
            name="slug",
            field=models.SlugField(
                db_index=True,
                help_text="URL va havolalarda ko‘rinadi (lotin harflar, raqam, tire).",
                max_length=80,
                unique=True,
            ),
        ),
    ]
