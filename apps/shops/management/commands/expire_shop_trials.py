from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.shops.models import Shop


class Command(BaseCommand):
    help = "Trial muddati o'tgan do'konlarni expired qiladi (cron)."

    def handle(self, *args, **options):
        now = timezone.now()
        qs = Shop.objects.filter(
            subscription_status=Shop.SubscriptionStatus.TRIAL,
            trial_ends_at__lt=now,
        )
        n = qs.update(subscription_status=Shop.SubscriptionStatus.EXPIRED)
        self.stdout.write(self.style.SUCCESS(f"Updated {n} shop(s) to expired."))
