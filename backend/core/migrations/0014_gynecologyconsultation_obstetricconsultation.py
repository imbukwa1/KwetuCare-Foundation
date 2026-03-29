from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_pediatricconsultation_diagnosis"),
    ]

    operations = [
        migrations.CreateModel(
            name="GynecologyConsultation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("presenting_complaints", models.TextField()),
                ("history_presenting_complaints", models.TextField()),
                ("antenatal_history", models.TextField()),
                ("obstetric_history", models.TextField()),
                ("gynecological_history", models.TextField()),
                ("sexual_reproductive_history", models.TextField()),
                ("past_medical_surgical_family_history", models.TextField()),
                ("examination_review_systems", models.TextField()),
                ("diagnosis", models.TextField()),
                ("treatment_plan", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.OneToOneField(on_delete=models.CASCADE, related_name="gynecology_consultation", to="core.patient")),
            ],
        ),
        migrations.CreateModel(
            name="ObstetricConsultation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("presenting_complaints", models.TextField()),
                ("history_presenting_complaints", models.TextField()),
                ("antenatal_history", models.TextField()),
                ("obstetric_history", models.TextField()),
                ("gynecological_history", models.TextField()),
                ("sexual_reproductive_history", models.TextField()),
                ("past_medical_surgical_family_history", models.TextField()),
                ("examination_review_systems", models.TextField()),
                ("diagnosis", models.TextField()),
                ("treatment_plan", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.OneToOneField(on_delete=models.CASCADE, related_name="obstetric_consultation", to="core.patient")),
            ],
        ),
    ]
