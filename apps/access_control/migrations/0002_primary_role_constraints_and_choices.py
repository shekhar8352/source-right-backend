from django.db import migrations, models


def migrate_org_member_to_viewer(apps, schema_editor):
    UserRole = apps.get_model("access_control", "UserRole")
    OrganizationInvite = apps.get_model("access_control", "OrganizationInvite")
    UserRole.objects.filter(role="ORG_MEMBER").update(role="VIEWER")
    OrganizationInvite.objects.filter(role="ORG_MEMBER").update(role="VIEWER")


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrate_org_member_to_viewer, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userrole",
            name="role",
            field=models.CharField(
                choices=[
                    ("ORG_ADMIN", "Organization Admin"),
                    ("FINANCE", "Finance"),
                    ("APPROVER", "Approver"),
                    ("VIEWER", "Viewer"),
                    ("VENDOR", "Vendor"),
                ],
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name="organizationinvite",
            name="role",
            field=models.CharField(
                choices=[
                    ("ORG_ADMIN", "Organization Admin"),
                    ("FINANCE", "Finance"),
                    ("APPROVER", "Approver"),
                    ("VIEWER", "Viewer"),
                    ("VENDOR", "Vendor"),
                ],
                max_length=40,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="userrole",
            name="uniq_user_org_role",
        ),
        migrations.AddConstraint(
            model_name="userrole",
            constraint=models.UniqueConstraint(
                fields=("user", "org"),
                name="uniq_user_org",
            ),
        ),
    ]
