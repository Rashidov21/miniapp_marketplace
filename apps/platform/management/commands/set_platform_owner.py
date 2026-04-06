from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    help = "Berilgan telegram_id foydalanuvchini platform_owner roliga o'tkazadi."

    def add_arguments(self, parser):
        parser.add_argument("telegram_id", type=int)

    def handle(self, *args, **options):
        tid = options["telegram_id"]
        u = User.objects.filter(telegram_id=tid).first()
        if not u:
            self.stderr.write(self.style.ERROR(f"User telegram_id={tid} not found."))
            return
        u.role = User.Role.PLATFORM_OWNER
        u.is_staff = True
        u.save(update_fields=["role", "is_staff"])
        self.stdout.write(self.style.SUCCESS(f"User {tid} is now platform_owner. Set password: python manage.py changepassword <telegram_id>"))
