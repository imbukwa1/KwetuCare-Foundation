from django.db import migrations, models


def forwards_update_doctor_role(apps, schema_editor):
    User = apps.get_model("core", "User")
    User.objects.filter(role="doctor").update(role="general_doctor")


def backwards_update_doctor_role(apps, schema_editor):
    User = apps.get_model("core", "User")
    User.objects.filter(role="general_doctor").update(role="doctor")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_patient_location_triage_bmi_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("registration", "Registration"),
                    ("nurse", "Nurse"),
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
        migrations.RunPython(
            forwards_update_doctor_role,
            backwards_update_doctor_role,
        ),
    ]
