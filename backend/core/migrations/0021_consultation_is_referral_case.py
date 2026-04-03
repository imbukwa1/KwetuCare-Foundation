from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_inventory_batches_and_camps"),
    ]

    operations = [
        migrations.AddField(
            model_name="consultation",
            name="is_referral_case",
            field=models.BooleanField(default=False),
        ),
    ]
