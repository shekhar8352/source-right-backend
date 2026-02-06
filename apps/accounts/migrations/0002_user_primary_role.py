from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="primary_role",
            field=models.CharField(
                choices=[
                    ("ORG_ADMIN", "Organization Admin"),
                    ("FINANCE", "Finance"),
                    ("APPROVER", "Approver"),
                    ("VIEWER", "Viewer"),
                    ("VENDOR", "Vendor"),
                ],
                default="VIEWER",
                max_length=40,
            ),
            preserve_default=False,
        ),
    ]
