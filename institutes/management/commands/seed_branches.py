"""
تعبئة الفروع (المعاهد) الجديدة دفعة واحدة.

الاستخدام:
    python manage.py seed_branches

- الأمر آمن يتكرر (idempotent) - بيستخدم get_or_create حسب الاسم، فلو الفرع
  موجود بالفعل مش هيتكرر.
- كود الفرع (INS0xx) ورقم الترخيص (LIC-10xx) بيتولدوا تلقائياً بالاستمرار
  من آخر رقم موجود في قاعدة البيانات وقت التشغيل.
- المدينة/المنطقة/العنوان/الجوال بقيم "TODO" مؤقتة - لازم تتراجع وتتحدث
  يدوياً من لوحة تحكم الأدمن (Institutes) بعد التشغيل.
"""
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from institutes.models import Institute


BRANCH_NAMES = [
    'فرع الدوادمي',
    'فرع الفاو خميس مشيط',
    'فرع الفاو – الرياض',
    'فرع الفاو – حفر الباطن',
    'فرع الفاو التخصصي القديم',
    'فرع آفاق التطور',
    'فرع الأهلي – عرعر',
    'فرع الأهلي – القريات',
    'فرع الأهلي – سكاكا',
    'فرع الثقة الدائمة',
    'فرع المورد الوافي',
    'فرع مؤسسة صرخة',
    'فرع الثقة الدائمة – طريف',
    'فرع المعهد الأهلي – المنصورية',
]


class Command(BaseCommand):
    help = 'تعبئة الفروع (المعاهد) الجديدة دفعة واحدة ببيانات أساسية مؤقتة'

    def _next_number(self, prefix, field):
        pattern = re.compile(rf'^{re.escape(prefix)}(\d+)$')
        max_num = 0
        for value in Institute.objects.values_list(field, flat=True):
            match = pattern.match(value or '')
            if match:
                max_num = max(max_num, int(match.group(1)))
        return max_num + 1

    @transaction.atomic
    def handle(self, *args, **options):
        next_code_num = self._next_number('INS', 'code')
        next_license_num = self._next_number('LIC-1', 'license_number')

        created_count = 0
        skipped_count = 0

        for name in BRANCH_NAMES:
            institute, created = Institute.objects.get_or_create(
                name=name,
                defaults={
                    'code': f'INS{next_code_num:03d}',
                    'license_number': f'LIC-1{next_license_num:03d}',
                    'address': 'TODO',
                    'city': 'TODO',
                    'region': 'TODO',
                    'phone': 'TODO',
                    'status': Institute.Status.ACTIVE,
                },
            )
            if created:
                created_count += 1
                next_code_num += 1
                next_license_num += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  + تم إنشاء: {institute.code} - {institute.name}'
                ))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(
                    f'  - موجود بالفعل، تم تخطيه: {institute.name}'
                ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'تم إنشاء {created_count} فرع جديد، وتخطي {skipped_count} فرع موجود مسبقاً.'
        ))
        if created_count:
            self.stdout.write(self.style.WARNING(
                'تنبيه: العنوان/المدينة/المنطقة/الجوال اتحطت بقيمة مؤقتة "TODO" '
                'لكل فرع جديد - لازم تتراجع وتتحدث من صفحة Institutes بلوحة تحكم الأدمن.'
            ))
