from django.db import migrations, models
from django.utils.text import slugify


def fill_product_slugs(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    for p in Product.objects.select_related("shop").all():
        base = slugify(p.name or "")[:80].strip("-") or "mahsulot"
        slug = base
        n = 0
        while Product.objects.filter(shop_id=p.shop_id).exclude(pk=p.pk).filter(slug=slug).exists():
            n += 1
            suffix = f"-{n}"
            slug = (base[: max(1, 80 - len(suffix))] + suffix).strip("-")
        p.slug = slug
        p.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0005_product_sort_order"),
        ("shops", "0007_shop_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="slug",
            field=models.SlugField(
                blank=True,
                db_index=True,
                help_text="URL va havolalarda (do‘kon ichida noyob).",
                max_length=120,
                null=True,
            ),
        ),
        migrations.RunPython(fill_product_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(
                db_index=True,
                help_text="URL va havolalarda (do‘kon ichida noyob).",
                max_length=120,
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("shop", "slug"),
                name="products_product_shop_slug_uniq",
            ),
        ),
    ]
