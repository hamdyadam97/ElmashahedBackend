import base64
import os
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.template import Context, Template
from django.conf import settings
from weasyprint import HTML
from io import BytesIO

from core.mixins import (
    EmployeeRequiredMixin, AdminRequiredMixin, BranchManagerRequiredMixin,
    InstituteScopedMixin, SearchMixin, FilterMixin
)
from programs.models import Diploma, Course
from .models import PermissionSlip, PermissionTemplate
from .utils import find_blocking_active_permission, blocking_info

logger = logging.getLogger('edu_system')


class PermissionListView(LoginRequiredMixin, InstituteScopedMixin, SearchMixin, FilterMixin, ListView):
    """قائمة الأذونات"""
    model = PermissionSlip
    template_name = 'permissions/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 20
    search_fields = ['permission_number', 'client__full_name', 'client__national_id']
    filter_fields = {'status': 'status'}
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # فلترة إضافية حسب نوع المستخدم
        if user.is_employee():
            queryset = queryset.filter(issued_by=user)
        
        return queryset.select_related('client', 'institute', 'issued_by', 'diploma', 'course').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = PermissionSlip.Status.choices
        return context


class PermissionCreateView(EmployeeRequiredMixin, CreateView):
    """إنشاء إذن جديد"""
    model = PermissionSlip
    template_name = 'permissions/permission_form.html'
    fields = ['client', 'diploma', 'course', 'study_mode', 'expiry_date', 'notes']
    success_url = reverse_lazy('permissions:permission_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        institute = user.institute or user.managed_institute

        # الدبلومة/الدورة لازم تكون مرتبطة فعلياً بمعهد الموظف (أو كل المعاهد لو أدمن/مدير إقليمي)
        if institute:
            form.fields['diploma'].queryset = Diploma.objects.filter(institutes=institute, status='active', is_deleted=False)
            form.fields['course'].queryset = Course.objects.filter(institutes=institute, status='active', is_deleted=False)
            form.fields['client'].queryset = institute.clients.filter(status='active', is_deleted=False)
        else:
            form.fields['diploma'].queryset = Diploma.objects.filter(status='active', is_deleted=False)
            form.fields['course'].queryset = Course.objects.filter(status='active', is_deleted=False)

        # اختياري - لو فاضي بناخد تاريخ انتهاء البرنامج تلقائياً (انظر form_valid)
        form.fields['expiry_date'].required = False
        form.fields['study_mode'].required = False

        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        context['clients'] = form.fields['client'].queryset
        context['diplomas'] = form.fields['diploma'].queryset
        context['courses'] = form.fields['course'].queryset
        return context
    
    def form_valid(self, form):
        user = self.request.user
        form.instance.issued_by = user

        # الإذن بيتربط بفرع الموظف اللي بيصدره، مش بفرع الدبلومة (اللي بقت متاحة لأكتر من فرع)
        if user.institute:
            form.instance.institute = user.institute
        elif user.managed_institute:
            form.instance.institute = user.managed_institute
        elif form.instance.client_id:
            form.instance.institute = form.instance.client.institute

        # منع إصدار إذن جديد لو عند الطالب إذن نشط بالفعل في معهد تاني
        blocking_permission = find_blocking_active_permission(form.instance.client, form.instance.institute_id)
        if blocking_permission:
            info = blocking_info(blocking_permission)
            form.add_error(
                None,
                f"يوجد للطالب إذن نشط بالفعل من معهد \"{info['institute_name']}\" "
                f"(رقم الإذن: {info['permission_number']}). "
                f"يجب التواصل مع {info['contact_name']} على {info['contact_phone'] or 'غير متوفر'} "
                f"لإلغاء الإذن القديم أولاً، ثم إعادة المحاولة."
            )
            return self.form_invalid(form)

        program = form.instance.diploma or form.instance.course

        if not form.instance.expiry_date:
            if program and program.end_date:
                form.instance.expiry_date = program.end_date
            else:
                form.instance.expiry_date = timezone.now().date() + timezone.timedelta(days=365)

        # طريقة الدراسة: لو البرنامج حضوري/أونلاين بس، نثبتها كده بصرف النظر عما أُرسل
        if program and program.study_mode != 'both':
            form.instance.study_mode = program.study_mode
        elif form.instance.study_mode not in ('offline', 'online'):
            form.instance.study_mode = ''

        messages.success(self.request, 'تم إصدار الإذن بنجاح')
        logger.info(f'Permission issued for {form.instance.client} by {self.request.user.username}')
        return super().form_valid(form)


class PermissionDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل الإذن"""
    model = PermissionSlip
    template_name = 'permissions/permission_detail.html'
    context_object_name = 'permission'


class PermissionPDFView(LoginRequiredMixin, View):
    """عرض PDF الإذن"""
    
    def get(self, request, pk):
        permission = get_object_or_404(PermissionSlip, pk=pk)
        
        # التحقق من الصلاحيات
        if not self._can_view_permission(request.user, permission):
            logger.warning(f'Unauthorized PDF access attempt by {request.user.username}')
            return HttpResponse('Unauthorized', status=403)
        
        try:
            pdf_buffer = generate_permission_pdf(permission)
            logger.info(f'PDF viewed for permission {permission.permission_number} by {request.user.username}')
            return HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        except Exception as e:
            logger.error(f'Error generating PDF: {str(e)}')
            return HttpResponse('Error generating PDF', status=500)
    
    def _can_view_permission(self, user, permission):
        if user.is_admin():
            return True
        if user.is_regional_manager():
            return permission.institute in user.managed_institutes.all()
        if user.is_branch_manager():
            return permission.institute == user.managed_institute
        if user.is_employee():
            return permission.issued_by == user
        return False


class PermissionDownloadView(LoginRequiredMixin, View):
    """تحميل PDF الإذن"""
    
    def get(self, request, pk):
        permission = get_object_or_404(PermissionSlip, pk=pk)
        
        if not PermissionPDFView()._can_view_permission(request.user, permission):
            logger.warning(f'Unauthorized PDF download attempt by {request.user.username}')
            return HttpResponse('Unauthorized', status=403)
        
        try:
            pdf_buffer = generate_permission_pdf(permission)
            logger.info(f'PDF downloaded for permission {permission.permission_number} by {request.user.username}')
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{permission.permission_number}.pdf"'
            return response
        except Exception as e:
            logger.error(f'Error generating PDF for download: {str(e)}')
            return HttpResponse('Error generating PDF', status=500)


class PermissionCancelView(BranchManagerRequiredMixin, View):
    """إلغاء الإذن"""
    
    def post(self, request, pk):
        permission = get_object_or_404(PermissionSlip, pk=pk)
        permission.status = PermissionSlip.Status.CANCELLED
        permission.save()
        logger.warning(f'Permission {permission.permission_number} cancelled by {request.user.username}')
        messages.success(request, 'تم إلغاء الإذن بنجاح')
        return redirect('permissions:permission_list')


# ==================== PDF Generation Functions ====================

def generate_default_pdf(permission):
    """دالة احتياطية لإنتاج PDF قياسي"""
    from django.template.loader import render_to_string
    
    context = {
        'permission': permission,
        'institute': permission.institute,
        'client': permission.client,
        'program': permission.get_program(),
        'issued_by': permission.issued_by,
    }
    
    html_content = render_to_string('permissions/default_permission.html', context)
    
    buffer = BytesIO()
    HTML(
        string=html_content,
        base_url=settings.BASE_DIR
    ).write_pdf(buffer)
    buffer.seek(0)
    return buffer


def get_b64(path):
    """Helper to convert image to base64"""
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    return ""


FONT_STACKS = {
    'arial': "'Arial', sans-serif",
    'cairo': "'Cairo', 'Arial', sans-serif",
}

# ملفات كل خط مضمّنة Base64 مباشرة داخل الـ CSS (زي صورة الخلفية بالظبط) بدل الاعتماد
# على url() نسبي، لأن تحليل base_url في WeasyPrint مش مضمون يفضل شغال على كل بيئة/سيرفر
CUSTOM_FONT_FILES = {
    'cairo': [('normal', 'Cairo-Regular.ttf'), ('bold', 'Cairo-Bold.ttf')],
}


def build_font_face_css(font_choice):
    files = CUSTOM_FONT_FILES.get(font_choice)
    if not files:
        return ''

    faces = []
    for weight, filename in files:
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', filename)
        font_b64 = get_b64(font_path)
        if not font_b64:
            continue
        faces.append(f"""
                    @font-face {{
                        font-family: '{font_choice.capitalize()}';
                        src: url('data:font/ttf;base64,{font_b64}');
                        font-weight: {weight};
                    }}
        """)
    return ''.join(faces)


def generate_permission_pdf(permission):
    """توليد PDF بناءً على قالب المعهد الخاص"""

    institute = permission.institute

    try:
        template_obj = institute.permission_template

        font_stack = FONT_STACKS.get(template_obj.font_family, FONT_STACKS['arial'])
        font_face_css = build_font_face_css(template_obj.font_family)

        background_css = ""
        background_html = ""
        if institute.background_img and os.path.exists(institute.background_img.path):
            institute_bg_b64 = get_b64(institute.background_img.path)
            background_css = f"""
                    .bg-watermark {{
                        position: fixed;
                        top: 0; left: 0; right: 0; bottom: 0;
                        width: 100%;
                        height: 100%;
                        background-image: url('data:image/png;base64,{institute_bg_b64}');
                        background-size: 100% 100%;
                        background-position: center;
                        background-repeat: no-repeat;
                        z-index: -1;
                    }}
            """
            background_html = '<div class="bg-watermark"></div>'

        custom_html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{ size: {template_obj.page_size} {template_obj.orientation}; margin: 0; }}
                    {font_face_css}
                    body {{ font-family: {font_stack}; direction: rtl; margin: 0; }}
                    .page-container {{ padding: 1.5cm; box-sizing: border-box; }}
                    {template_obj.custom_css}
                    {background_css}
                </style>
            </head>
            <body>
                {background_html}
                <div class="page-container">
                    <header>{template_obj.header_content}</header>
                    <main>{template_obj.body_content}</main>
                    <footer>{template_obj.footer_content}</footer>
                </div>
            </body>
        </html>
        """
    except PermissionTemplate.DoesNotExist:
        return generate_default_pdf(permission)
    
    # تحويل القالب
    django_template = Template(custom_html)
    
    # تحميل الصور
    tvtc_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'TVTC.jpg')
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'ahley_bg.jpg')
    bg_path1 = os.path.join(settings.BASE_DIR, 'static', 'images', 'Afaq.jpg')

    context = Context({
        'permission': permission,
        'client': permission.client,
        'institute': institute,
        'program': permission.get_program(),
        'issued_by': permission.issued_by,
        'today': timezone.now().date(),
        
    })
    
    try:
        final_html = django_template.render(context)

        buffer = BytesIO()
        HTML(
            string=final_html,
            base_url=settings.BASE_DIR
        ).write_pdf(buffer)
    except Exception as e:
        logger.error(f"Custom PDF template failed for institute {institute.code}: {e}")
        return generate_default_pdf(permission)

    # Debug
    if institute.logo:
        logger.debug(f"Logo Path: {institute.logo.path}, Exists: {os.path.exists(institute.logo.path)}")

    buffer.seek(0)
    return buffer


# ==================== Template Views ====================

class TemplateListView(AdminRequiredMixin, ListView):
    """قائمة قوالب PDF"""
    model = PermissionTemplate
    template_name = 'permissions/template_list.html'
    context_object_name = 'templates'


class TemplateCreateView(AdminRequiredMixin, CreateView):
    """إنشاء قالب PDF جديد"""
    model = PermissionTemplate
    template_name = 'permissions/template_form.html'
    fields = [
        'institute', 'header_content', 'body_content', 'footer_content',
        'custom_css', 'page_size', 'orientation'
    ]
    success_url = reverse_lazy('permissions:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء القالب بنجاح')
        logger.info(f'PDF template created for {form.instance.institute.name}')
        return super().form_valid(form)


class TemplateUpdateView(AdminRequiredMixin, UpdateView):
    """تعديل قالب PDF"""
    model = PermissionTemplate
    template_name = 'permissions/template_form.html'
    fields = [
        'header_content', 'body_content', 'footer_content',
        'custom_css', 'page_size', 'orientation'
    ]
    success_url = reverse_lazy('permissions:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث القالب بنجاح')
        logger.info(f'PDF template updated for {form.instance.institute.name}')
        return super().form_valid(form)


# ==================== Client Response View ====================

def client_respond_view(request, pk, response_status):
    """دالة تستقبل رد العميل من الإيميل"""
    permission = get_object_or_404(PermissionSlip, pk=pk)
    
    if response_status == 'confirmed':
        permission.status = 'active'
        message = "شكراً لك! تم تأكيد استلامك للإذن بنجاح."
        logger.info(f'Permission {permission.permission_number} confirmed by client')
    elif response_status == 'cancelled':
        permission.status = 'cancelled'
        message = "تم تسجيل رفضك للإذن. سيتم التواصل معك من قبل الإدارة."
        logger.warning(f'Permission {permission.permission_number} cancelled by client')
    else:
        message = "حدث خطأ في معالجة طلبك."
    
    permission.save()
    
    return render(request, 'programs/response_thank_you.html', {
        'message': message,
        'permission': permission
    })
