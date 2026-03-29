from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_druginventory_amount"),
    ]

    operations = [
        migrations.RenameField(
            model_name="patient",
            old_name="village",
            new_name="location",
        ),
        migrations.AddField(
            model_name="triage",
            name="bmi",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="triage",
            name="height",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name="triage",
            name="respiratory_rate",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="triage",
            name="spo2",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
