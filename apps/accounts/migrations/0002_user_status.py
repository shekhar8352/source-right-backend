from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="status",
            field=models.CharField(
                choices=[("ACTIVE", "Active"), ("INACTIVE", "Inactive")],
                default="ACTIVE",
                max_length=20,
            ),
        ),
    ]
