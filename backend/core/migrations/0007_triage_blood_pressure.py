from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_patient_child_age_patient_child_date_of_birth_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="triage",
            name="blood_pressure",
            field=models.CharField(default="120/80", max_length=20),
            preserve_default=False,
        ),
    ]
