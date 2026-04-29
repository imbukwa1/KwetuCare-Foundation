from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_druginventory_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="approval_rejection_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="approved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verification_attempts",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verification_code_hash",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verification_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verification_locked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="is_email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="rejected_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
