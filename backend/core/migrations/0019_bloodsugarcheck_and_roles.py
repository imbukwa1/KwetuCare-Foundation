from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_dentalconsultation"),
    ]

    operations = [
        migrations.CreateModel(
            name="BloodSugarCheck",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("blood_sugar_level", models.DecimalField(decimal_places=2, max_digits=6)),
                ("test_type", models.CharField(choices=[("fasting", "Fasting"), ("random", "Random")], max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "patient",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blood_sugar_check",
                        to="core.patient",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="patient",
            name="status",
            field=models.CharField(
                choices=[
                    ("triage", "Triage"),
                    ("blood_sugar", "Blood Sugar"),
                    ("doctor", "Doctor"),
                    ("pharmacy", "Pharmacy"),
                    ("complete", "Complete"),
                ],
                default="triage",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("registration", "Registration"),
                    ("nurse", "Nurse"),
                    ("blood_sugar", "Blood Sugar Department"),
                    ("general_doctor", "General Doctor"),
                    ("pediatrician", "Pediatrician"),
                    ("gynecologist", "Gynecologist"),
                    ("obstetrician", "Obstetrician"),
                    ("nutritionist", "Nutritionist"),
                    ("dental", "Dentist"),
                    ("optician", "Optician"),
                    ("pharmacist", "Pharmacist"),
                    ("admin", "Admin"),
                ],
                max_length=20,
            ),
        ),
    ]
