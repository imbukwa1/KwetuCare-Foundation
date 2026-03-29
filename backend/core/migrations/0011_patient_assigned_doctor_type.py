from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_expand_user_specialist_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="assigned_doctor_type",
            field=models.CharField(
                choices=[
                    ("general_doctor", "General Doctor"),
                    ("pediatrician", "Pediatrician"),
                    ("gynecologist", "Gynecologist"),
                    ("obstetrician", "Obstetrician"),
                    ("nutritionist", "Nutritionist"),
                    ("dental", "Dentist"),
                    ("optician", "Optician"),
                ],
                default="general_doctor",
                max_length=20,
            ),
        ),
    ]
