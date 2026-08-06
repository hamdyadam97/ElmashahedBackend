from django.db import migrations


def copy_institute_forward(apps, schema_editor):
    Diploma = apps.get_model('programs', 'Diploma')
    Course = apps.get_model('programs', 'Course')

    for diploma in Diploma.objects.all():
        if diploma.institute_id:
            diploma.institutes.add(diploma.institute_id)

    for course in Course.objects.all():
        if course.institute_id:
            course.institutes.add(course.institute_id)


def copy_institute_backward(apps, schema_editor):
    Diploma = apps.get_model('programs', 'Diploma')
    Course = apps.get_model('programs', 'Course')

    for diploma in Diploma.objects.all():
        first_institute = diploma.institutes.first()
        if first_institute:
            diploma.institute_id = first_institute.id
            diploma.save(update_fields=['institute'])

    for course in Course.objects.all():
        first_institute = course.institutes.first()
        if first_institute:
            course.institute_id = first_institute.id
            course.save(update_fields=['institute'])


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0005_add_institutes_m2m'),
    ]

    operations = [
        migrations.RunPython(copy_institute_forward, copy_institute_backward),
    ]
