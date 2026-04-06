"""Create demo sellers, shops, and products."""
from decimal import Decimal
from io import BytesIO

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image

from apps.products.models import Product
from apps.shops.models import Shop
from apps.users.models import User


def _jpeg_placeholder():
    buf = BytesIO()
    Image.new("RGB", (320, 320), color=(13, 148, 136)).save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return buf.read()


class Command(BaseCommand):
    help = "Load sample sellers and products (minimal placeholder images)."

    def handle(self, *args, **options):
        seller1, _ = User.objects.update_or_create(
            telegram_id=100001,
            defaults={
                "first_name": "Dilshod",
                "last_name": "Demo",
                "username": "seller_demo_1",
                "role": User.Role.SELLER,
            },
        )
        seller2, _ = User.objects.update_or_create(
            telegram_id=100002,
            defaults={
                "first_name": "Madina",
                "last_name": "Demo",
                "username": "seller_demo_2",
                "role": User.Role.SELLER,
            },
        )
        shop1, _ = Shop.objects.update_or_create(
            owner=seller1,
            defaults={"name": "Qo‘lda ishlangan sovg‘alar", "is_active": True, "is_verified": True},
        )
        shop2, _ = Shop.objects.update_or_create(
            owner=seller2,
            defaults={"name": "Dropship elektronika", "is_active": True, "is_verified": False},
        )

        jpeg = _jpeg_placeholder()

        def ensure_product(shop, name, price, desc):
            p = Product.objects.filter(shop=shop, name=name).first()
            if not p:
                p = Product(
                    shop=shop,
                    name=name,
                    price=Decimal(price),
                    description=desc,
                    is_active=True,
                )
                p.image.save("placeholder.jpg", ContentFile(jpeg), save=False)
                p.save()
            elif not p.image:
                p.image.save("placeholder.jpg", ContentFile(jpeg), save=True)
            return p

        ensure_product(shop1, "Tilla rangli savat", "120000.00", "Qo‘lda to‘qilgan, sovg‘a uchun.")
        ensure_product(shop1, "Ipak sharf", "89000.00", "Yumshoq ipak, turli ranglar.")
        ensure_product(shop2, "Simli quloqchin", "150000.00", "Bluetooth 5, shovqin bosish.")
        ensure_product(shop2, "USB-C kabel", "35000.00", "1m, tez zaryad.")

        self.stdout.write(self.style.SUCCESS("Sample data ready. Shops: %s, %s" % (shop1.id, shop2.id)))
