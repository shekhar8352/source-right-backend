from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationInvite",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("email", models.EmailField(max_length=254)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("ORG_ADMIN", "Organization Admin"),
                            ("ORG_MEMBER", "Organization Member"),
                        ],
                        max_length=40,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("INVITED", "Invited"), ("ACTIVE", "Active")],
                        default="INVITED",
                        max_length=20,
                    ),
                ),
                ("token", models.CharField(max_length=64, unique=True)),
                ("invited_at", models.DateTimeField(auto_now_add=True)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "accepted_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accepted_organization_invites",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sent_organization_invites",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        db_column="org_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invites",
                        to="organizations.organization",
                        to_field="org_id",
                    ),
                ),
            ],
            options={
                "db_table": "organization_invites",
            },
        ),
        migrations.AddConstraint(
            model_name="organizationinvite",
            constraint=models.UniqueConstraint(
                fields=("org", "email"),
                name="uniq_org_invite_email",
            ),
        ),
        migrations.AddIndex(
            model_name="organizationinvite",
            index=models.Index(fields=["org", "status"], name="idx_invites_org_status"),
        ),
        migrations.AddIndex(
            model_name="organizationinvite",
            index=models.Index(fields=["email"], name="idx_invites_email"),
        ),
    ]
