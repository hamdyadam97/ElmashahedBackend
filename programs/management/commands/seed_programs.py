"""
تعبئة بيانات الدبلومات والدورات الافتراضية.

الاستخدام:
    python manage.py seed_programs
    python manage.py seed_programs --institute INS001
    python manage.py seed_programs --institute 3

- ما بيحطش أسعار أو تواريخ (بتتحط لاحقاً من لوحة التحكم).
- طريقة الدراسة (study_mode) لكل السجلات = both (حضوري أو أونلاين).
- الأمر آمن يتكرر (idempotent) - بيستخدم update_or_create حسب الكود.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from institutes.models import Institute
from programs.models import Diploma, Course, StudyMode


DIPLOMAS = [
    # (code, name, hours, duration_text, duration_months)
    ('DIP-001', 'إدارة التمريض', 81, 'سنتين ونصف', 30),
    ('DIP-002', 'إدارة المستشفيات', 87, 'سنتين ونصف', 30),
    ('DIP-003', 'حماية البيئة', 80, 'سنتين ونصف', 30),
    ('DIP-004', 'السلامة والصحة المهنية', 82, 'سنتين ونصف', 30),
    ('DIP-005', 'الأمن السيبراني', 83, 'سنتين ونصف', 30),
    ('DIP-006', 'الموارد البشرية', 79, 'سنتين ونصف', 30),
    ('DIP-007', 'الإدارة المكتبية', 80, 'سنتين ونصف', 30),
    ('DIP-008', 'علوم الحاسب الآلي', 86, 'سنتين ونصف', 30),
    ('DIP-009', 'الحاسب وتقنية المكتبات', 31, 'سنة واحدة', 12),
]

COURSES = [
    # (code, name, hours, duration_text, duration_months)
    ('CRS-001', 'الأرشفة الإلكترونية', 660, None, None),
    ('CRS-002', 'إدارة مكتبية', 432, None, None),
    ('CRS-003', 'إدخال البيانات ومعالجة النصوص', 240, None, None),
    ('CRS-004', 'الإدارة المكتبية المتقدمة', 360, None, None),
    ('CRS-005', 'استخدام الحاسب', 120, None, None),
    ('CRS-006', 'إدارة مكتبية', 120, None, None),
    ('CRS-007', 'اللغة الإنجليزية (تأسيسية)', None, '3 أشهر', 3),
    ('CRS-008', 'اللغة الإنجليزية (متوسطة)', None, '6 أشهر', 6),
    ('CRS-009', 'اللغة الإنجليزية (متقدمة)', None, '9 أشهر', 9),
    ('CRS-010', 'القدرات العامة', None, '30 يوم', 1),
    ('CRS-011', 'التحصيلي (رياضيات - فيزياء - كيمياء - أحياء)', None, None, None),
]


class Command(BaseCommand):
    help = 'تعبئة بيانات الدبلومات والدورات الافتراضية (بدون أسعار أو تواريخ)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--institute',
            type=str,
            default=None,
            help='كود أو رقم المعهد اللي هتتسجل تحته البيانات (افتراضياً أول معهد نشط)',
        )

    def _resolve_institute(self, value):
        if value:
            institute = Institute.objects.filter(code=value).first()
            if not institute and value.isdigit():
                institute = Institute.objects.filter(pk=int(value)).first()
            if not institute:
                raise CommandError(f'لم يتم العثور على معهد بالكود/الرقم: {value}')
            return institute

        institute = Institute.objects.filter(status='active').order_by('id').first()
        if not institute:
            raise CommandError('لا يوجد أي معهد نشط في النظام - أنشئ معهد أولاً.')
        return institute

    @transaction.atomic
    def handle(self, *args, **options):
        institute = self._resolve_institute(options.get('institute'))
        self.stdout.write(f'المعهد المستخدم: {institute.name} ({institute.code})')

        diplomas_created, diplomas_updated = 0, 0
        for code, name, hours, duration_text, duration_months in DIPLOMAS:
            defaults = {
                'name': name,
                'hours': hours,
                'duration': duration_text,
                'study_mode': StudyMode.BOTH,
            }
            if duration_months:
                defaults['duration_months'] = duration_months

            obj, created = Diploma.objects.update_or_create(code=code, defaults=defaults)
            obj.institutes.add(institute)
            if created:
                diplomas_created += 1
            else:
                diplomas_updated += 1

        courses_created, courses_updated = 0, 0
        for code, name, hours, duration_text, duration_months in COURSES:
            defaults = {
                'name': name,
                'hours': hours,
                'duration': duration_text,
                'study_mode': StudyMode.BOTH,
            }
            if duration_months:
                defaults['duration_months'] = duration_months

            obj, created = Course.objects.update_or_create(code=code, defaults=defaults)
            obj.institutes.add(institute)
            if created:
                courses_created += 1
            else:
                courses_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'الدبلومات: {diplomas_created} جديدة، {diplomas_updated} محدَّثة.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'الدورات: {courses_created} جديدة، {courses_updated} محدَّثة.'
        ))
        self.stdout.write(self.style.WARNING(
            'ملاحظة: الأسعار والتواريخ لسه فاضية - أدخلها من لوحة التحكم لكل دبلومة/دورة قبل ما تفتح باب التسجيل.'
        ))
