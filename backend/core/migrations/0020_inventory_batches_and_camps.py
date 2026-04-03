from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone
import django.db.models.deletion


def create_initial_batches(apps, schema_editor):
    DrugInventory = apps.get_model("core", "DrugInventory")
    DrugBatch = apps.get_model("core", "DrugBatch")

    future_expiry = timezone.localdate() + timedelta(days=365)

    for inventory in DrugInventory.objects.all():
        if not getattr(inventory, "camp", None):
            inventory.camp = "General"
            inventory.save(update_fields=["camp"])

        if inventory.stock_quantity > 0 and not DrugBatch.objects.filter(inventory=inventory).exists():
            DrugBatch.objects.create(
                inventory=inventory,
                quantity_received=inventory.stock_quantity,
                quantity_remaining=inventory.stock_quantity,
                expiry_date=future_expiry,
                status="active",
            )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_bloodsugarcheck_and_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="druginventory",
            name="camp",
            field=models.CharField(default="General", max_length=255),
        ),
        migrations.AlterField(
            model_name="druginventory",
            name="drug_name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterModelOptions(
            name="druginventory",
            options={"ordering": ["camp", "drug_name", "amount"]},
        ),
        migrations.CreateModel(
            name="DrugBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity_received", models.PositiveIntegerField()),
                ("quantity_remaining", models.PositiveIntegerField()),
                ("expiry_date", models.DateField()),
                ("status", models.CharField(choices=[("active", "Active"), ("expired", "Expired"), ("depleted", "Depleted")], default="active", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("inventory", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="core.druginventory")),
            ],
            options={"ordering": ["expiry_date", "created_at", "id"]},
        ),
        migrations.RunPython(create_initial_batches, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="druginventory",
            constraint=models.UniqueConstraint(fields=("camp", "drug_name", "amount"), name="unique_inventory_per_camp_drug_amount"),
        ),
    ]
