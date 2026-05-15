from django.db import migrations


def set_affects_true(apps, schema_editor):
    Asset = apps.get_model('tracker', 'Asset')

    Asset.objects.filter(
        affects_contribution_room__isnull=True
    ).update(
        affects_contribution_room=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0003_contribution_asset_and_more'),  # Django will set this automatically
    ]

    operations = [
        migrations.RunPython(set_affects_true),
    ]