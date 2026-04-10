from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shops", "0005_seed_subscription_plans"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="subscriptionpayment",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="pending"),
                fields=("shop",),
                name="uniq_subscriptionpayment_pending_per_shop",
            ),
        ),
    ]
