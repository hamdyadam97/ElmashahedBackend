from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('institutes', '0003_institute_background_img_and_more'),
        ('programs', '0004_course_duration_course_hours_course_study_mode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='diploma',
            name='institutes',
            field=models.ManyToManyField(
                related_name='diplomas_m2m',
                to='institutes.institute',
                verbose_name='Institutes',
                help_text='Institutes offering this diploma - can be more than one',
            ),
        ),
        migrations.AddField(
            model_name='course',
            name='institutes',
            field=models.ManyToManyField(
                related_name='courses_m2m',
                to='institutes.institute',
                verbose_name='Institutes',
                help_text='Institutes offering this course - can be more than one',
            ),
        ),
    ]
