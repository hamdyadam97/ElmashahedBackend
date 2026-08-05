from django.db import migrations


def backfill_referral_code(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.filter(referral_code__isnull=True).order_by('id'):
        user.referral_code = f"EMP{user.pk:03d}"
        user.save(update_fields=['referral_code'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_referral_code'),
    ]

    operations = [
        migrations.RunPython(backfill_referral_code, noop_reverse),
    ]
