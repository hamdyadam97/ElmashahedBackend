import base64

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.template import Context, Template
from weasyprint import HTML
from django.conf import settings
from .models import PermissionSlip, PermissionTemplate
from accounts.views import EmployeeRequiredMixin, AdminRequiredMixin, BranchManagerRequiredMixin
from io import BytesIO
import os


class PermissionListView(LoginRequiredMixin, ListView):
    """قائمة الأذونات"""
    model = PermissionSlip
    template_name = 'permissions/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin():
            queryset = PermissionSlip.objects.all()
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = PermissionSlip.objects.filter(institute__in=institutes)
        elif user.is_branch_manager():
            queryset = PermissionSlip.objects.filter(institute=user.managed_institute) if user.managed_institute else PermissionSlip.objects.none()
        elif user.is_employee():
            queryset = PermissionSlip.objects.filter(issued_by=user)
        else:
            queryset = PermissionSlip.objects.none()
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(permission_number__icontains=search) |
                Q(client__full_name__icontains=search) |
                Q(client__national_id__icontains=search)
            )
        
        # تصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('client', 'institute', 'issued_by', 'diploma', 'course').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = PermissionSlip.Status.choices
        return context


class PermissionCreateView(EmployeeRequiredMixin, CreateView):
    """إنشاء إذن جديد"""
    model = PermissionSlip
    template_name = 'permissions/permission_form.html'
    fields = ['client', 'diploma', 'course', 'expiry_date', 'notes']
    success_url = reverse_lazy('permissions:permission_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # تصفية الخيارات داخل الفورم (عشان الأمان عند الحفظ)
        if user.institute:
            form.fields['diploma'].queryset = user.institute.diplomas.filter(status='active', is_deleted=False)
            form.fields['course'].queryset = user.institute.courses.filter(status='active', is_deleted=False)
            form.fields['client'].queryset = user.institute.clients.filter(status='active', is_deleted=False)

        return form

    # --- هذا هو الجزء الذي ينقصك ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # نأخذ الخيارات المفلترة من الفورم ونرسلها للقالب بالأسماء التي استخدمتها
        form = self.get_form()
        context['clients'] = form.fields['client'].queryset
        context['diplomas'] = form.fields['diploma'].queryset
        context['courses'] = form.fields['course'].queryset
        return context

    # ------------------------------

    def form_valid(self, form):
        form.instance.issued_by = self.request.user
        form.instance.institute = self.request.user.institute

        if not form.instance.expiry_date:
            program = form.instance.diploma or form.instance.course
            if program:
                form.instance.expiry_date = program.end_date
            else:

                from django.utils import timezone
                form.instance.expiry_date = timezone.now().date() + timezone.timedelta(days=365)

        messages.success(self.request, f'تم إصدار الإذن بنجاح')
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
        user = request.user
        if not (user.is_admin() or 
                user.is_regional_manager() and permission.institute in user.managed_institutes.all() or
                user.is_branch_manager() and permission.institute == user.managed_institute or
                user.is_employee() and permission.issued_by == user):
            return HttpResponse('Unauthorized', status=403)
        
        # إنشاء PDF
        pdf_buffer = generate_permission_pdf(permission)
        
        return HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')


class PermissionDownloadView(LoginRequiredMixin, View):
    """تحميل PDF الإذن"""
    
    def get(self, request, pk):
        permission = get_object_or_404(PermissionSlip, pk=pk)
        
        # التحقق من الصلاحيات
        user = request.user
        if not (user.is_admin() or 
                user.is_regional_manager() and permission.institute in user.managed_institutes.all() or
                user.is_branch_manager() and permission.institute == user.managed_institute or
                user.is_employee() and permission.issued_by == user):
            return HttpResponse('Unauthorized', status=403)
        
        # إنشاء PDF
        pdf_buffer = generate_permission_pdf(permission)
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{permission.permission_number}.pdf"'
        return response


class PermissionCancelView(BranchManagerRequiredMixin, View):
    """إلغاء الإذن"""
    
    def post(self, request, pk):
        permission = get_object_or_404(PermissionSlip, pk=pk)
        permission.status = PermissionSlip.Status.CANCELLED
        permission.save()
        messages.success(request, 'تم إلغاء الإذن بنجاح')
        return redirect('permissions:permission_list')


def generate_default_pdf(permission):
    """دالة احتياطية لإنتاج PDF قياسي في حال عدم وجود قالب خاص بالمعهد"""
    from weasyprint import HTML
    from django.template.loader import render_to_string
    from django.conf import settings

    # هنا بننادي على قالب HTML ثابت إحنا عاملينه في ملفات المشروع
    # القالب ده موجود في: templates/permissions/pdf/default_permission.html
    context = {
        'permission': permission,
        'institute': permission.institute,
        'client': permission.client,
        'program': permission.get_program(),
        'issued_by': permission.issued_by,
    }

    # تحويل القالب لـ String
    html_content = render_to_string('permissions/pdf/default_permission.html', context)

    buffer = BytesIO()
    # تحويل الـ HTML لـ PDF
    HTML(string=html_content, base_url=settings.MEDIA_ROOT).write_pdf(buffer)

    buffer.seek(0)
    return buffer



from django.conf import settings
def generate_permission_pdf(permission):
    """توليد PDF بناءً على قالب المعهد الخاص"""

    institute = permission.institute
    # جلب القالب المرتبط بالمعهد
    try:
        template_obj = institute.permission_template
        # تجميع الـ HTML من القالب المخزن في قاعدة البيانات
        custom_html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{ size: {template_obj.page_size} {template_obj.orientation}; margin: 1cm; }}
                    body {{ font-family: 'Arial', sans-serif; direction: rtl; }}
                    {template_obj.custom_css}
                </style>
            </head>
            <body>
                <header>{template_obj.header_content}</header>
                <main>{template_obj.body_content}</main>
                <footer>{template_obj.footer_content}</footer>
            </body>
        </html>
        """
    except PermissionTemplate.DoesNotExist:
        # إذا لم يوجد قالب للمعهد، استخدم قالب نظام افتراضي
        return generate_default_pdf(permission)

    # تحويل الـ String إلى قالب Django ليعالج المتغيرات مثل {{ client.full_name }}
    django_template = Template(custom_html)
    vision_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'vision2030.png')
    tvtc_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'TVTC.jpg')
    vision_base64 = ""
    tvtc_base64 = ""
    if os.path.exists(vision_path):
        with open(vision_path, "rb") as f:
            vision_base64 = base64.b64encode(f.read()).decode('utf-8')

    if os.path.exists(tvtc_path):
        with open(tvtc_path, "rb") as f:
            tvtc_base64 = base64.b64encode(f.read()).decode('utf-8')

    def get_b64(path):
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        return ""

    # صورة الخلفية (تأكد من وضعها في مجلد static/images باسم afaq_bg.jpg أو حسب اسم ملفك)
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'ahley_bg.jpg')
    # تجهيز البيانات
    context = Context({
        'permission': permission,
        'client': permission.client,
        'institute': institute,
        'program': permission.get_program(),
        'issued_by': permission.issued_by,
        'today': timezone.now().date(),
        'vision_logo': vision_base64,  # نمرره في الكونتكست
        'tvtc_logo': tvtc_base64,  # نمرره في الكونتكست
        'bg_b64': get_b64(bg_path),  # تمرير كود الخلفية
    })

    # معالجة القالب بالبيانات
    final_html = django_template.render(context)

    # توليد الـ PDF
    buffer = BytesIO()

    HTML(string=final_html, base_url=settings.MEDIA_ROOT).write_pdf(buffer)
    if institute.logo:
        print(f"Logo Path: {institute.logo.path}")
        print(f"Exists: {os.path.exists(institute.logo.path)}")
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
        return super().form_valid(form)





def client_respond_view(request, pk, response_status):
    """دالة تستقبل رد العميل من الإيميل (موافق/مرفوض)"""
    permission = get_object_or_404(PermissionSlip, pk=pk)

    if response_status == 'confirmed':
        permission.status = 'active'  # أو الحالة التي ترغبين بها عند القبول
        message = "شكراً لك! تم تأكيد استلامك للإذن بنجاح."
    elif response_status == 'cancelled':
        permission.status = 'cancelled'
        message = "تم تسجيل رفضك للإذن. سيتم التواصل معك من قبل الإدارة."
    else:
        message = "حدث خطأ في معالجة طلبك."

    permission.save()

    # سنحتاج لإنشاء صفحة بسيطة تظهر للعميل بعد الضغط
    return render(request, 'programs/response_thank_you.html', {
        'message': message,
        'permission': permission
    })