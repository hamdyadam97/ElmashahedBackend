from django.http import HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from core.utils import get_pdf_response
from permissions.models import PermissionTemplate
from accounts.views import AdminRequiredMixin
import pandas as pd
from django.shortcuts import redirect
from django.contrib import messages
from .models import Institute

class InstituteListView(LoginRequiredMixin, ListView):
    """قائمة المعاهد"""
    model = Institute
    template_name = 'institutes/institute_list.html'
    context_object_name = 'institutes'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin():
            queryset = Institute.objects.all()
        elif user.is_regional_manager():
            queryset = user.managed_institutes.all()
        elif user.is_branch_manager():
            queryset = Institute.objects.filter(id=user.managed_institute.id) if user.managed_institute else Institute.objects.none()
        elif user.is_employee():
            queryset = Institute.objects.filter(id=user.institute.id) if user.institute else Institute.objects.none()
        else:
            queryset = Institute.objects.none()
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(city__icontains=search)
            )
        
        # تصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Institute.Status.choices
        return context


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
        return super().form_valid(form)


class InstituteDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل المعهد"""
    model = Institute
    template_name = 'institutes/institute_detail.html'
    context_object_name = 'institute'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        institute = self.get_object()
        
        # إحصائيات المعهد
        context['diplomas_count'] = institute.diplomas.filter(status='active').count()
        context['courses_count'] = institute.courses.filter(status='active').count()
        context['clients_count'] = institute.clients.count()
        context['permissions_count'] = institute.permissions.count()
        context['employees_count'] = institute.employees.filter(role='employee').count()
        
        # آخر الأذونات
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
        return super().form_valid(form)


class InstituteDeleteView(AdminRequiredMixin, DeleteView):
    """أرشفة المعهد (حذف ناعم)"""
    model = Institute
    template_name = 'institutes/institute_confirm_delete.html'
    success_url = reverse_lazy('institutes:institute_list')

    def post(self, request, *args, **kwargs):
        # 1. جلب المعهد
        self.object = self.get_object()

        # 2. تنفيذ الحذف الناعم للمعهد نفسه
        self.object.soft_delete()

        # 3. (لمسة احترافية) إخفاء العناصر المرتبطة (Cascading Soft Delete)
        # إذا كان الموديل في BaseModel يدعم العلاقات، سيتم إخفاء كورسات المعهد أيضاً
        if hasattr(self.object, 'courses'):
            self.object.courses.all().update(is_deleted=True)

        messages.success(request, f'تم نقل معهد "{self.object.name}" وجميع بياناته المرتبطة إلى الأرشيف.')
        return redirect(self.get_success_url())

    def delete(self, request, *args, **kwargs):
        """تحويل أي طلب حذف قادم من الكلاس الأصلي إلى دالة الـ post المعدلة"""
        return self.post(request, *args, **kwargs)


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
    fields = []  # We'll handle this manually
    
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
        
        # Get or create template
        template, created = PermissionTemplate.objects.get_or_create(
            institute=institute,
            defaults={
                'header_content': '',
                'body_content': '',
                'footer_content': ''
            }
        )
        
        # Update template
        template.header_content = request.POST.get('header_content', '')
        template.body_content = request.POST.get('body_content', '')
        template.footer_content = request.POST.get('footer_content', '')
        template.custom_css = request.POST.get('custom_css', '')
        template.page_size = request.POST.get('page_size', 'A4')
        template.orientation = request.POST.get('orientation', 'portrait')
        template.save()
        
        messages.success(request, 'تم تحديث قالب PDF بنجاح')
        return redirect('institutes:pdf_template', pk=institute.pk)
    
    def get_success_url(self):
        return reverse_lazy('institutes:pdf_template', kwargs={'pk': self.object.pk})



def upload_data(request):
    if request.method == "POST" and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        try:
            # نقرأ الملف سواء CSV أو Excel
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

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
            messages.success(request, "تم رفع البيانات بنجاح.")
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء رفع البيانات: {str(e)}")
    return redirect('institutes:institute_list')




def export_excel(request):
    institutes = Institute.objects.all().values(
        'code', 'name', 'license_number', 'address', 'city', 'region', 'phone', 'email'
    )
    df = pd.DataFrame(list(institutes))

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="institutes.xlsx"'
    df.to_excel(response, index=False)
    return response





def export_institutes_pdf(request):
    institutes = Institute.objects.all()
    return get_pdf_response(request, 'institutes/institutes_pdf_template.html',
                          {'institutes': institutes, 'title': 'تقرير المعاهد المسجلة'}, 'institutes_report')
