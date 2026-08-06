import logging

from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST

from institutes.models import Institute
from programs.models import Diploma
from clients.models import Client
from accounts.models import User
from permissions.models import PermissionSlip

logger = logging.getLogger('edu_system')


def _resolve_referral_employee(ref_code):
    """يبحث عن موظف نشط يملك referral_code مطابق، بدون كشف هويته للزائر"""
    if not ref_code:
        return None
    return User.objects.filter(
        referral_code__iexact=ref_code,
        role=User.Role.EMPLOYEE,
        is_active=True
    ).first()


class LandingView(View):
    """صفحة إصدار المشهد العامة - بدون تسجيل دخول"""

    def get(self, request, ref_code=None):
        ref_code = ref_code or request.GET.get('ref', '')
        # نتحقق من صلاحية الكود بصمت فقط، لا نعرض اسم الموظف للزائر أبداً
        employee = _resolve_referral_employee(ref_code)
        valid_ref_code = ref_code if employee else ''

        # لو الموظف مرتبط بفرع معين، نحدده تلقائياً بدل ما الزائر يختار
        preselected_institute_id = ''
        if employee and employee.institute_id and employee.institute.status == Institute.Status.ACTIVE:
            preselected_institute_id = employee.institute_id

        institutes = Institute.objects.filter(status=Institute.Status.ACTIVE).order_by('name')

        return render(request, 'portal/landing.html', {
            'preselected_institute_id': preselected_institute_id,
            'institutes': institutes,
            'ref_code': valid_ref_code,
        })


def api_diplomas(request):
    """AJAX: قائمة الدبلومات النشطة - متاحة لكل الفروع بصرف النظر عن الفرع المختار"""
    institute_id = request.GET.get('institute_id')
    if not institute_id:
        return JsonResponse({'results': []})

    diplomas = Diploma.objects.filter(
        status='active',
        is_deleted=False
    ).order_by('name').values('id', 'name', 'duration_months')

    return JsonResponse({'results': list(diplomas)})


def api_search_client(request):
    """AJAX: البحث عن طالب برقم الهوية/الإقامة داخل معهد معين"""
    national_id = (request.GET.get('national_id') or '').strip()
    institute_id = request.GET.get('institute_id')

    if not national_id or not institute_id:
        return JsonResponse({'found': False})

    client = Client.objects.filter(
        national_id=national_id,
        institute_id=institute_id,
        is_deleted=False,
        status='active'
    ).first()

    if not client:
        return JsonResponse({'found': False})

    return JsonResponse({
        'found': True,
        'client': {
            'id': client.id,
            'full_name': client.full_name,
            'national_id': client.national_id,
            'phone': client.phone,
        }
    })


REQUIRED_REGISTER_FIELDS = ['first_name', 'last_name', 'gender', 'birth_date', 'phone']


@require_POST
def api_register_client(request):
    """AJAX: تسجيل طالب جديد بصمت لو مش موجود، ثم إرجاعه زي نتيجة البحث"""
    national_id = (request.POST.get('national_id') or '').strip()
    institute_id = request.POST.get('institute_id')
    ref_code = (request.POST.get('ref_code') or '').strip()

    if not national_id or not institute_id:
        return JsonResponse({'success': False, 'error': 'بيانات ناقصة.'}, status=400)

    institute = Institute.objects.filter(pk=institute_id, status=Institute.Status.ACTIVE).first()
    if not institute:
        return JsonResponse({'success': False, 'error': 'الفرع غير صالح.'}, status=400)

    errors = {}
    for field in REQUIRED_REGISTER_FIELDS:
        if not (request.POST.get(field) or '').strip():
            errors[field] = 'مطلوب'
    if request.POST.get('gender') not in ('male', 'female'):
        errors['gender'] = 'مطلوب'
    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    if Client.objects.filter(national_id=national_id).exists():
        return JsonResponse({
            'success': False,
            'error': 'يوجد بالفعل حساب بهذا الرقم، برجاء التواصل مع المعهد.'
        }, status=409)

    employee = _resolve_referral_employee(ref_code)

    try:
        client = Client.objects.create(
            national_id=national_id,
            institute=institute,
            first_name=request.POST.get('first_name').strip(),
            last_name=request.POST.get('last_name').strip(),
            gender=request.POST.get('gender'),
            birth_date=request.POST.get('birth_date'),
            phone=request.POST.get('phone').strip(),
            email=(request.POST.get('email') or '').strip(),
            city=(request.POST.get('city') or '').strip(),
            sector=(request.POST.get('sector') or '').strip(),
            registered_by=employee,
        )
    except IntegrityError:
        return JsonResponse({
            'success': False,
            'error': 'يوجد بالفعل حساب بهذا الرقم، برجاء التواصل مع المعهد.'
        }, status=409)

    logger.info(f'Public self-registration: client {client.national_id} at institute {institute.code}')

    return JsonResponse({
        'success': True,
        'client': {
            'id': client.id,
            'full_name': client.full_name,
            'national_id': client.national_id,
            'phone': client.phone,
        }
    })


class IssueView(View):
    """إصدار المشهد فعلياً وإرجاع الـ PDF مباشرة - بنفس منطق الإصدار الداخلي"""

    def get(self, request):
        return HttpResponseNotAllowed(['POST'])

    def post(self, request):
        client_id = request.POST.get('client_id')
        diploma_id = request.POST.get('diploma_id')
        ref_code = (request.POST.get('ref_code') or '').strip()

        client = get_object_or_404(Client, pk=client_id, is_deleted=False)
        diploma = get_object_or_404(Diploma, pk=diploma_id, is_deleted=False, status='active')

        employee = _resolve_referral_employee(ref_code)

        permission = PermissionSlip(
            client=client,
            diploma=diploma,
            expiry_date=diploma.end_date or (timezone.now().date() + timezone.timedelta(days=365)),
            issued_by=None,
            issued_from_public=True,
            referral_employee=employee,
            referral_code=ref_code if employee else '',
        )
        permission.save()

        logger.info(
            f'Public permission {permission.permission_number} issued for client {client.national_id} '
            f'(ref={ref_code or "-"})'
        )

        from permissions.views import generate_permission_pdf
        pdf_buffer = generate_permission_pdf(permission)

        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{permission.permission_number}.pdf"'
        return response
