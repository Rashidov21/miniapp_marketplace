from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="seller_terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="seller_terms_version",
            field=models.CharField(blank=True, help_text="Last accepted marketplace / seller terms version (empty = not accepted).", max_length=16),
        ),
    ]
