from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_patient_assigned_doctor_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="PediatricConsultation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("presenting_complaint", models.TextField()),
                ("history_presenting_illness", models.TextField()),
                ("past_medical_history", models.TextField()),
                ("prenatal_antenatal_history", models.TextField()),
                ("birth_history", models.TextField()),
                ("nutritional_history", models.TextField()),
                ("growth_development_history", models.TextField()),
                ("family_social_history", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "patient",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="pediatric_consultation",
                        to="core.patient",
                    ),
                ),
            ],
        ),
    ]
