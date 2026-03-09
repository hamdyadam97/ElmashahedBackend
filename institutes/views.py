from django.http import HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import redirect
from django.contrib import messages
import pandas as pd
import logging

from core.mixins import (
    AdminRequiredMixin, InstituteScopedMixin,
    SearchMixin, FilterMixin, SoftDeleteMixin
)
from core.utils import get_pdf_response
from permissions.models import PermissionTemplate
from .models import Institute

logger = logging.getLogger('edu_system')


class InstituteListView(LoginRequiredMixin, SearchMixin, FilterMixin, ListView):
    """قائمة المعاهد"""
    model = Institute
    template_name = 'institutes/institute_list.html'
    context_object_name = 'institutes'
    paginate_by = 20
    search_fields = ['name', 'code', 'city']
    filter_fields = {'status': 'status'}
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # فلترة حسب صلاحيات المستخدم
        if user.is_admin():
            pass  # See all
        elif user.is_regional_manager():
            queryset = user.managed_institutes.all()
        elif user.is_branch_manager() and user.managed_institute:
            queryset = queryset.filter(id=user.managed_institute.id)
        elif user.is_employee() and user.institute:
            queryset = queryset.filter(id=user.institute.id)
        else:
            queryset = queryset.none()
        
        return queryset.order_by('name')


class InstituteCreateView(AdminRequiredMixin, CreateView):
    """إنشاء معهد جديد"""
    model = Institute
    template_name = 'institutes/institute_form.html'
    fields = [
        'name', 'code', 'license_number', 'address', 'city', 'region',
        'phone', 'email', 'logo', 'header_image', 'footer_text',
        'signature_image', 'stamp_image', 'status'
    ]
    success_url = reverse_lazy('institutes:institute_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'تم إنشاء المعهد {form.instance.name} بنجاح')
        logger.info(f'Institute {form.instance.name} created by {self.request.user.username}')
        return super().form_valid(form)


class InstituteDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل المعهد"""
    model = Institute
    template_name = 'institutes/institute_detail.html'
    context_object_name = 'institute'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        institute = self.get_object()
        
        context['diplomas_count'] = institute.diplomas.filter(status='active').count()
        context['courses_count'] = institute.courses.filter(status='active').count()
        context['clients_count'] = institute.clients.count()
        context['permissions_count'] = institute.permissions.count()
        context['employees_count'] = institute.employees.filter(role='employee').count()
        context['recent_permissions'] = institute.permissions.select_related(
            'client'
        ).order_by('-created_at')[:10]
        
        return context


class InstituteUpdateView(AdminRequiredMixin, UpdateView):
    """تعديل المعهد"""
    model = Institute
    template_name = 'institutes/institute_form.html'
    fields = [
        'name', 'code', 'license_number', 'address', 'city', 'region',
        'phone', 'email', 'logo', 'header_image', 'footer_text',
        'signature_image', 'stamp_image', 'status'
    ]
    
    def get_success_url(self):
        return reverse_lazy('institutes:institute_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث المعهد بنجاح')
        logger.info(f'Institute {form.instance.name} updated by {self.request.user.username}')
        return super().form_valid(form)


class InstituteDeleteView(AdminRequiredMixin, SoftDeleteMixin, DeleteView):
    """أرشفة المعهد (حذف ناعم)"""
    model = Institute
    template_name = 'institutes/institute_confirm_delete.html'
    success_url = reverse_lazy('institutes:institute_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        institute_name = self.object.name
        
        # الحذف الناعم للمعهد
        self.object.soft_delete()
        
        # حذف ناعم للكورسات المرتبطة
        if hasattr(self.object, 'courses'):
            self.object.courses.all().update(is_deleted=True)
        if hasattr(self.object, 'diplomas'):
            self.object.diplomas.all().update(is_deleted=True)
        
        logger.warning(f'Institute {institute_name} archived by {request.user.username}')
        messages.success(request, f'تم نقل معهد "{institute_name}" وجميع بياناته المرتبطة إلى الأرشيف.')
        return redirect(self.success_url)


# ==================== PDF Template Views ====================

class PDFTemplateView(LoginRequiredMixin, DetailView):
    """عرض قالب PDF"""
    model = Institute
    template_name = 'institutes/institutes_pdf_template.html'
    context_object_name = 'institute'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        institute = self.get_object()
        
        try:
            context['template'] = institute.permission_template
        except PermissionTemplate.DoesNotExist:
            context['template'] = None
        
        return context


class PDFTemplateEditView(AdminRequiredMixin, UpdateView):
    """تعديل قالب PDF"""
    model = Institute
    template_name = 'institutes/pdf_template_form.html'
    fields = []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        institute = self.get_object()
        
        try:
            template = institute.permission_template
        except PermissionTemplate.DoesNotExist:
            template = None
        
        context['template'] = template
        return context
    
    def post(self, request, *args, **kwargs):
        institute = self.get_object()
        
        template, created = PermissionTemplate.objects.get_or_create(
            institute=institute,
            defaults={
                'header_content': '',
                'body_content': '',
                'footer_content': ''
            }
        )
        
        template.header_content = request.POST.get('header_content', '')
        template.body_content = request.POST.get('body_content', '')
        template.footer_content = request.POST.get('footer_content', '')
        template.custom_css = request.POST.get('custom_css', '')
        template.page_size = request.POST.get('page_size', 'A4')
        template.orientation = request.POST.get('orientation', 'portrait')
        template.save()
        
        logger.info(f'PDF template for {institute.name} updated by {request.user.username}')
        messages.success(request, 'تم تحديث قالب PDF بنجاح')
        return redirect('institutes:pdf_template', pk=institute.pk)


# ==================== Import/Export Views ====================

def upload_data(request):
    """استيراد المعاهد من Excel/CSV"""
    if request.method != "POST" or not request.FILES.get('file'):
        return redirect('institutes:institute_list')
    
    uploaded_file = request.FILES['file']
    
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        items_created = 0
        for _, row in df.iterrows():
            Institute.objects.update_or_create(
                code=row['code'],
                defaults={
                    'name': row['name'],
                    'license_number': row.get('license_number', ''),
                    'address': row.get('address', ''),
                    'city': row.get('city', ''),
                    'region': row.get('region', ''),
                    'phone': row.get('phone', ''),
                    'email': row.get('email', ''),
                }
            )
            items_created += 1
        
        logger.info(f'{items_created} institutes imported by {request.user.username}')
        messages.success(request, f"تم رفع {items_created} معهد بنجاح.")
    except Exception as e:
        logger.error(f'Error importing institutes: {str(e)}')
        messages.error(request, f"حدث خطأ أثناء رفع البيانات: {str(e)}")
    
    return redirect('institutes:institute_list')


def export_excel(request):
    """تصدير المعاهد لـ Excel"""
    try:
        institutes = Institute.objects.all().values(
            'code', 'name', 'license_number', 'address', 'city', 'region', 'phone', 'email'
        )
        df = pd.DataFrame(list(institutes))
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="institutes.xlsx"'
        df.to_excel(response, index=False)
        
        logger.info(f'Institutes exported by {request.user.username}')
        return response
    except Exception as e:
        logger.error(f'Error exporting institutes: {str(e)}')
        messages.error(request, "حدث خطأ أثناء التصدير")
        return redirect('institutes:institute_list')


def export_institutes_pdf(request):
    """تصدير المعاهد لـ PDF"""
    institutes = Institute.objects.all()
    return get_pdf_response(
        request,
        'institutes/institutes_pdf_template.html',
        {'institutes': institutes, 'title': 'تقرير المعاهد المسجلة'},
        'institutes_report'
    )
