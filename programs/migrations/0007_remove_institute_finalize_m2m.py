from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0006_copy_institute_to_institutes'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='course',
            name='programs_co_institu_f7e831_idx',
        ),
        migrations.RemoveIndex(
            model_name='diploma',
            name='programs_di_institu_74dfd3_idx',
        ),
        migrations.RemoveField(
            model_name='diploma',
            name='institute',
        ),
        migrations.RemoveField(
            model_name='course',
            name='institute',
        ),
        migrations.AlterField(
            model_name='diploma',
            name='institutes',
            field=models.ManyToManyField(
                related_name='diplomas',
                to='institutes.institute',
                verbose_name='Institutes',
                help_text='Institutes offering this diploma - can be more than one',
            ),
        ),
        migrations.AlterField(
            model_name='course',
            name='institutes',
            field=models.ManyToManyField(
                related_name='courses',
                to='institutes.institute',
                verbose_name='Institutes',
                help_text='Institutes offering this course - can be more than one',
            ),
        ),
        migrations.AddIndex(
            model_name='diploma',
            index=models.Index(fields=['status'], name='programs_di_status_d336a6_idx'),
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['status'], name='programs_co_status_a0093c_idx'),
        ),
    ]
