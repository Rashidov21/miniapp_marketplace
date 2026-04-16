from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.products.cache_utils import (
    bump_product_list_cache_version,
    product_public_cache_key,
)
from apps.products.models import Product
from apps.shops.models import Shop


def _bust_product(shop_id: int, product_id: int) -> None:
    cache.delete(product_public_cache_key(shop_id, product_id))


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def invalidate_product_public_cache(sender, instance: Product, **kwargs):
    _bust_product(instance.shop_id, instance.pk)
    bump_product_list_cache_version(instance.shop_id)


@receiver(post_save, sender=Shop)
def invalidate_shop_products_public_cache(sender, instance: Shop, **kwargs):
    bump_product_list_cache_version(instance.pk)
    for pid in Product.objects.filter(shop=instance).values_list("pk", flat=True):
        _bust_product(instance.pk, pid)
