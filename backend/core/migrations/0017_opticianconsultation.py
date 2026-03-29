from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_merge_20260329_2155"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpticianConsultation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("presenting_complaint", models.TextField()),
                ("ocular_history", models.TextField()),
                ("visual_symptoms_functional_impact", models.TextField()),
                ("past_ocular_medical_history", models.TextField()),
                ("medication_allergy_eye_drop_history", models.TextField()),
                ("examination_vision_assessment", models.TextField()),
                ("diagnosis", models.TextField()),
                ("treatment_plan", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.OneToOneField(on_delete=models.CASCADE, related_name="optician_consultation", to="core.patient")),
            ],
        ),
    ]
