from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_triage_blood_pressure"),
    ]

    operations = [
        migrations.AddField(
            model_name="druginventory",
            name="amount",
            field=models.CharField(default="N/A", max_length=50),
            preserve_default=False,
        ),
    ]
