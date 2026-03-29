from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_opticianconsultation"),
    ]

    operations = [
        migrations.CreateModel(
            name="DentalConsultation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("presenting_complaint", models.TextField()),
                ("history_presenting_illness", models.TextField()),
                ("oral_examination", models.TextField()),
                ("oral_hygiene_practices", models.TextField()),
                ("past_dental_history", models.TextField()),
                ("medical_history", models.TextField()),
                ("diagnosis", models.TextField()),
                ("treatment_plan", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.OneToOneField(on_delete=models.CASCADE, related_name="dental_consultation", to="core.patient")),
            ],
        ),
    ]
