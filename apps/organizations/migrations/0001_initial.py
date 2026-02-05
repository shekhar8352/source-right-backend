from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import apps.organizations.domain.identifiers


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "org_id",
                    models.CharField(
                        primary_key=True,
                        serialize=False,
                        editable=False,
                        max_length=40,
                        default=apps.organizations.domain.identifiers.generate_org_id,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("country", models.CharField(max_length=3)),
                ("base_currency", models.CharField(max_length=3)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("SUSPENDED", "Suspended"),
                            ("DELETED", "Deleted"),
                        ],
                        default="ACTIVE",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_organizations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "organizations",
            },
        ),
    ]
