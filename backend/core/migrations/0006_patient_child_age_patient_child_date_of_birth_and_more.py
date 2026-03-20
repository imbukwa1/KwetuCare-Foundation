from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_druginventory"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="child_age",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="child_date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="child_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="patient",
            name="guardian_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="patient",
            name="has_child",
            field=models.BooleanField(default=False),
        ),
    ]
