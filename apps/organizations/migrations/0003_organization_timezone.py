from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_organization_invite"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="timezone",
            field=models.CharField(default="UTC", max_length=64),
        ),
    ]
