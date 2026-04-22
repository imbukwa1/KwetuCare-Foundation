from django.db import migrations, models


def infer_category(name):
    value = (name or "").strip().lower()
    if value in {"paracetamol", "ibuprofen", "diclofenac", "aspirin", "naproxen", "tramadol"}:
        return "analgesics"
    if value in {"amoxicillin", "amoxiciline", "azithromycin", "ciprofloxacin", "metronidazole", "doxycycline"}:
        return "antibiotics"
    if value in {"artemether", "lumefantrine", "artemether-lumefantrine", "quinine"}:
        return "antimalarials"
    if value in {"cetirizine", "chlorpheniramine", "loratadine"}:
        return "antihistamines"
    if value in {"fluconazole", "clotrimazole", "nystatin"}:
        return "antifungals"
    if value in {"acyclovir", "oseltamivir"}:
        return "antivirals"
    if value in {"omeprazole", "pantoprazole", "oral rehydration salts", "ors", "loperamide"}:
        return "gastrointestinal"
    if value in {"salbutamol", "aminophylline"}:
        return "respiratory"
    if value in {"vitamin a", "vitamin c", "folic acid", "iron", "zinc"}:
        return "supplements"
    if value in {"bcg", "opv", "measles vaccine", "tt vaccine"}:
        return "vaccines"
    if value in {"oxytocin", "misoprostol", "oral contraceptive pills"}:
        return "hormonal"
    if value in {"amlodipine", "atenolol", "furosemide"}:
        return "cardiovascular"
    if value in {"acetaminophen"}:
        return "antipyretics"
    return "other"


def backfill_categories(apps, schema_editor):
    DrugInventory = apps.get_model("core", "DrugInventory")
    for item in DrugInventory.objects.all():
        item.category = infer_category(item.drug_name)
        item.save(update_fields=["category"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0021_consultation_is_referral_case"),
    ]

    operations = [
        migrations.AddField(
            model_name="druginventory",
            name="category",
            field=models.CharField(
                choices=[
                    ("analgesics", "Analgesics (Painkillers)"),
                    ("antibiotics", "Antibiotics"),
                    ("antimalarials", "Antimalarials"),
                    ("antihistamines", "Antihistamines"),
                    ("antipyretics", "Antipyretics"),
                    ("antifungals", "Antifungals"),
                    ("antivirals", "Antivirals"),
                    ("gastrointestinal", "Gastrointestinal Drugs"),
                    ("respiratory", "Respiratory Drugs"),
                    ("supplements", "Supplements"),
                    ("vaccines", "Vaccines"),
                    ("hormonal", "Hormonal Drugs"),
                    ("cardiovascular", "Cardiovascular Drugs"),
                    ("other", "Other"),
                ],
                default="other",
                max_length=30,
            ),
        ),
        migrations.RunPython(backfill_categories, migrations.RunPython.noop),
    ]
