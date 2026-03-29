from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_pediatricconsultation"),
    ]

    operations = [
        migrations.AddField(
            model_name="pediatricconsultation",
            name="diagnosis",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
