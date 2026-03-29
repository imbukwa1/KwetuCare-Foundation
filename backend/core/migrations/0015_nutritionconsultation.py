from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_gynecologyconsultation_obstetricconsultation"),
    ]

    operations = [
        migrations.CreateModel(
            name="NutritionConsultation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("presenting_complaint", models.TextField()),
                ("dietary_history", models.TextField()),
                ("nutritional_assessment", models.TextField()),
                ("medical_health_conditions", models.TextField()),
                ("child_feeding_history", models.TextField(blank=True)),
                ("lifestyle_assessment", models.TextField()),
                ("nutrition_diagnosis", models.CharField(choices=[("undernutrition", "Undernutrition"), ("overnutrition", "Overnutrition"), ("balanced", "Balanced")], max_length=20)),
                ("risk_level", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High")], max_length=20)),
                ("nutrition_plan", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.OneToOneField(on_delete=models.CASCADE, related_name="nutrition_consultation", to="core.patient")),
            ],
        ),
    ]
