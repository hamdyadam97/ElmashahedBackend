import logging

from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404
from django.views import View

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

        institutes = Institute.objects.filter(status=Institute.Status.ACTIVE).order_by('name')

        return render(request, 'portal/landing.html', {
            'institutes': institutes,
            'ref_code': valid_ref_code,
        })


def api_diplomas(request):
    """AJAX: قائمة الدبلومات النشطة لمعهد معين"""
    institute_id = request.GET.get('institute_id')
    if not institute_id:
        return JsonResponse({'results': []})

    diplomas = Diploma.objects.filter(
        institute_id=institute_id,
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


class IssueView(View):
    """إصدار المشهد فعلياً وإرجاع الـ PDF مباشرة - بنفس منطق الإصدار الداخلي"""

    def get(self, request):
        return HttpResponseNotAllowed(['POST'])

    def post(self, request):
        client_id = request.POST.get('client_id')
        diploma_id = request.POST.get('diploma_id')
        ref_code = (request.POST.get('ref_code') or '').strip()

        client = get_object_or_404(Client, pk=client_id, is_deleted=False)
        diploma = get_object_or_404(Diploma, pk=diploma_id, is_deleted=False)

        # حماية إضافية: التأكد إن الطالب والدبلوم من نفس المعهد
        if client.institute_id != diploma.institute_id:
            return HttpResponse('Invalid selection', status=400)

        employee = _resolve_referral_employee(ref_code)

        permission = PermissionSlip(
            client=client,
            diploma=diploma,
            expiry_date=diploma.end_date,
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
