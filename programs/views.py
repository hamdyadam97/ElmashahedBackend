from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
from datetime import date
import pandas as pd
import logging

from core.mixins import (
    AdminRequiredMixin, BranchManagerRequiredMixin, EmployeeRequiredMixin,
    InstituteScopedMixin, InstituteScopedRegistrationMixin,
    SearchMixin, FilterMixin, SoftDeleteMixin
)
from core.utils import get_pdf_response
from institutes.models import Institute
from .models import Diploma, Course, ProgramCategory, ProgramRegistration

logger = logging.getLogger('edu_system')


# ==================== Category Views ====================

class CategoryListView(LoginRequiredMixin, ListView):
    """قائمة الفئات"""
    model = ProgramCategory
    template_name = 'programs/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(AdminRequiredMixin, CreateView):
    """إنشاء فئة جديدة"""
    model = ProgramCategory
    template_name = 'programs/category_form.html'
    fields = ['name', 'type', 'description']
    success_url = reverse_lazy('programs:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء الفئة بنجاح')
        logger.info(f'Category {form.instance.name} created by {self.request.user.username}')
        return super().form_valid(form)


class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    """تعديل فئة"""
    model = ProgramCategory
    template_name = 'programs/category_form.html'
    fields = ['name', 'type', 'description']
    success_url = reverse_lazy('programs:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الفئة بنجاح')
        logger.info(f'Category {form.instance.name} updated by {self.request.user.username}')
        return super().form_valid(form)


class ProgramCategoryDeleteView(AdminRequiredMixin, SoftDeleteMixin, DeleteView):
    """حذف ناعم للفئة"""
    model = ProgramCategory
    template_name = 'programs/category_confirm_delete.html'
    success_url = reverse_lazy('programs:category_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        category_name = self.object.name
        
        self.object.soft_delete()
        
        if hasattr(self.object, 'diplomas'):
            self.object.diplomas.all().update(is_deleted=True)
        if hasattr(self.object, 'courses'):
            self.object.courses.all().update(is_deleted=True)
        
        logger.warning(f'Category {category_name} archived by {request.user.username}')
        messages.warning(request, f'تم أرشفة الفئة "{category_name}" وجميع البرامج التابعة لها.')
        return redirect(self.success_url)


# ==================== Base Program Views (Diploma & Course) ====================

class BaseProgramListView(LoginRequiredMixin, InstituteScopedMixin, SearchMixin, FilterMixin, ListView):
    """Base View for Diploma and Course List"""
    paginate_by = 20
    search_fields = ['name', 'code']
    filter_fields = {'status': 'status'}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = self.model.Status.choices
        return context


class BaseProgramCreateView(BranchManagerRequiredMixin, CreateView):
    """Base View for creating Diploma or Course"""
    fields = [
        'institute', 'name', 'code', 'description', 'category', 'duration_months',
        'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
        'fees', 'status'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_admin():
            context['institutes'] = Institute.objects.all()
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        if user.is_branch_manager() and user.managed_institute:
            form.instance.institute = user.managed_institute
            if 'institute' in form.fields:
                del form.fields['institute']
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, f'تم إنشاء {self.get_program_type()} {form.instance.name} بنجاح')
        logger.info(f'{self.get_program_type()} {form.instance.name} created by {self.request.user.username}')
        return super().form_valid(form)
    
    def get_program_type(self):
        return 'البرنامج'


class BaseProgramUpdateView(BranchManagerRequiredMixin, UpdateView):
    """Base View for updating Diploma or Course"""
    fields = [
        'institute', 'name', 'code', 'description', 'category', 'duration_months',
        'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
        'fees', 'status'
    ]
    
    def get_success_url(self):
        return reverse_lazy(self.detail_url_name, kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'تم التحديث بنجاح')
        logger.info(f'{self.get_program_type()} {form.instance.name} updated by {self.request.user.username}')
        return super().form_valid(form)
    
    def get_program_type(self):
        return 'البرنامج'


class BaseProgramDeleteView(BranchManagerRequiredMixin, SoftDeleteMixin, DeleteView):
    """Base View for soft deleting Diploma or Course"""
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        program_name = self.object.name
        self.object.soft_delete()
        logger.warning(f'{self.get_program_type()} {program_name} archived by {request.user.username}')
        messages.success(request, f'تم نقل "{program_name}" للأرشيف.')
        return redirect(self.success_url)
    
    def get_program_type(self):
        return 'البرنامج'


# ==================== Diploma Views ====================

class DiplomaListView(BaseProgramListView):
    """قائمة الدبلومات"""
    model = Diploma
    template_name = 'programs/diploma_list.html'
    context_object_name = 'diplomas'


class DiplomaCreateView(BaseProgramCreateView):
    """إنشاء دبلومة جديدة"""
    model = Diploma
    template_name = 'programs/diploma_form.html'
    success_url = reverse_lazy('programs:diploma_list')
    
    def get_program_type(self):
        return 'الدبلومة'


class DiplomaDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل الدبلومة"""
    model = Diploma
    template_name = 'programs/diploma_detail.html'
    context_object_name = 'diploma'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        diploma = self.get_object()
        
        context['registrations_count'] = diploma.registrations.count()
        context['registrations'] = diploma.registrations.select_related(
            'client', 'registered_by'
        ).order_by('-created_at')[:20]
        
        return context


class DiplomaUpdateView(BaseProgramUpdateView):
    """تعديل الدبلومة"""
    model = Diploma
    template_name = 'programs/diploma_form.html'
    detail_url_name = 'programs:diploma_detail'
    
    def get_program_type(self):
        return 'الدبلومة'


class DiplomaDeleteView(BaseProgramDeleteView):
    """حذف ناعم للدبلومة"""
    model = Diploma
    template_name = 'programs/diploma_confirm_delete.html'
    success_url = reverse_lazy('programs:diploma_list')
    
    def get_program_type(self):
        return 'الدبلومة'


# ==================== Course Views ====================

class CourseListView(BaseProgramListView):
    """قائمة الدورات"""
    model = Course
    template_name = 'programs/course_list.html'
    context_object_name = 'courses'


class CourseCreateView(BaseProgramCreateView):
    """إنشاء دورة جديدة"""
    model = Course
    template_name = 'programs/course_form.html'
    success_url = reverse_lazy('programs:course_list')
    
    def get_program_type(self):
        return 'الدورة'


class CourseDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل الدورة"""
    model = Course
    template_name = 'programs/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        context['registrations_count'] = course.registrations.count()
        context['registrations'] = course.registrations.select_related(
            'client', 'registered_by'
        ).order_by('-created_at')[:20]
        
        return context


class CourseUpdateView(BaseProgramUpdateView):
    """تعديل الدورة"""
    model = Course
    template_name = 'programs/course_form.html'
    detail_url_name = 'programs:course_detail'
    
    def get_program_type(self):
        return 'الدورة'


class CourseDeleteView(BaseProgramDeleteView):
    """حذف ناعم للدورة"""
    model = Course
    template_name = 'programs/course_confirm_delete.html'
    success_url = reverse_lazy('programs:course_list')
    
    def get_program_type(self):
        return 'الدورة'


# ==================== Registration Views ====================

class RegistrationListView(LoginRequiredMixin, InstituteScopedRegistrationMixin, FilterMixin, ListView):
    """قائمة التسجيلات"""
    model = ProgramRegistration
    template_name = 'programs/registration_list.html'
    context_object_name = 'registrations'
    paginate_by = 20
    filter_fields = {'status': 'status'}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = ProgramRegistration.Status.choices
        return context


class RegistrationCreateView(EmployeeRequiredMixin, CreateView):
    """إنشاء تسجيل جديد"""
    model = ProgramRegistration
    template_name = 'programs/registration_form.html'
    fields = ['client', 'diploma', 'course', 'status', 'notes']
    success_url = reverse_lazy('programs:registration_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        if user.institute:
            form.fields['diploma'].queryset = user.institute.diplomas.filter(status='active')
            form.fields['course'].queryset = user.institute.courses.filter(status='active')
        
        return form
    
    def form_valid(self, form):
        form.instance.registered_by = self.request.user
        messages.success(self.request, 'تم تسجيل العميل بنجاح')
        logger.info(f'Registration created for {form.instance.client} by {self.request.user.username}')
        return super().form_valid(form)


class RegistrationDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل التسجيل"""
    model = ProgramRegistration
    template_name = 'programs/registration_detail.html'
    context_object_name = 'registration'


# ==================== Import/Export Functions ====================

def _get_institute_id(row, user):
    """Helper to get institute ID from row or user"""
    inst_id = row.get('institute')
    if not inst_id:
        if hasattr(user, 'institute') and user.institute:
            inst_id = user.institute_id
        elif hasattr(user, 'managed_institute') and user.managed_institute:
            inst_id = user.managed_institute_id
    return inst_id


def _clean_date(val, fallback=None):
    """Helper to clean date values"""
    if pd.notnull(val) and str(val) != 'NaT':
        return val.date() if hasattr(val, 'date') else val
    return fallback


def upload_diplomas(request):
    """استيراد الدبلومات من Excel/CSV"""
    if request.method != "POST" or not request.FILES.get('file'):
        return redirect('programs:diploma_list')
    
    uploaded_file = request.FILES['file']
    user = request.user
    
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        
        date_columns = ['start_date', 'end_date', 'registration_start_date', 'registration_end_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        items_created = 0
        for _, row in df.iterrows():
            inst_id = _get_institute_id(row, user)
            cat_id = row.get('category')
            
            if not inst_id or not Institute.objects.filter(id=inst_id).exists():
                continue
            if cat_id and not ProgramCategory.objects.filter(id=cat_id).exists():
                continue
            
            Diploma.objects.update_or_create(
                code=row['code'],
                defaults={
                    'name': row['name'],
                    'description': row.get('description', ''),
                    'institute_id': inst_id,
                    'category_id': cat_id,
                    'duration_months': row.get('duration_months', 24),
                    'fees': row.get('fees', 0.00),
                    'start_date': row.get('start_date'),
                    'end_date': row.get('end_date'),
                    'registration_start_date': row.get('registration_start_date'),
                    'registration_end_date': row.get('registration_end_date'),
                    'status': row.get('status', 'active'),
                }
            )
            items_created += 1
        
        if items_created > 0:
            logger.info(f'{items_created} diplomas imported by {user.username}')
            messages.success(request, f"تم رفع {items_created} دبلومة بنجاح.")
        else:
            messages.warning(request, "لم يتم رفع أي بيانات. تأكد من صحة المعرفات.")
    
    except Exception as e:
        logger.error(f'Error importing diplomas: {str(e)}')
        messages.error(request, f"حدث خطأ: {str(e)}")
    
    return redirect('programs:diploma_list')


def upload_courses(request):
    """استيراد الدورات من Excel/CSV"""
    if request.method != "POST" or not request.FILES.get('file'):
        return redirect('programs:course_list')
    
    uploaded_file = request.FILES['file']
    user = request.user
    
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        date_cols = ['start_date', 'end_date', 'registration_start_date', 'registration_end_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        items_created = 0
        for _, row in df.iterrows():
            inst_id = _get_institute_id(row, user)
            cat_id = row.get('category')
            code = str(row.get('code', '')).strip()
            
            if not code or not inst_id or not Institute.objects.filter(id=inst_id).exists():
                continue
            
            s_date = _clean_date(row.get('start_date'), date.today())
            e_date = _clean_date(row.get('end_date'), s_date)
            
            Course.objects.update_or_create(
                code=code,
                defaults={
                    'name': row.get('name'),
                    'description': row.get('description', ''),
                    'institute_id': inst_id,
                    'category_id': cat_id,
                    'duration_months': row.get('duration_months', 6),
                    'fees': row.get('fees', 0.00),
                    'start_date': s_date,
                    'end_date': e_date,
                    'registration_start_date': _clean_date(row.get('registration_start_date'), s_date),
                    'registration_end_date': _clean_date(row.get('registration_end_date'), e_date),
                    'status': row.get('status', 'active'),
                }
            )
            items_created += 1
        
        logger.info(f'{items_created} courses imported by {user.username}')
        messages.success(request, f"تم رفع {items_created} دورة بنجاح.")
    
    except Exception as e:
        logger.error(f'Error importing courses: {str(e)}')
        messages.error(request, f"حدث خطأ: {str(e)}")
    
    return redirect('programs:course_list')


def export_diplomas_excel(request):
    """تصدير الدبلومات لـ Excel"""
    try:
        data = []
        for d in Diploma.objects.all():
            data.append({
                'الكود': d.code,
                'الاسم': d.name,
                'المعهد': d.institute.name,
                'الفئة': d.category.name if d.category else '',
                'الرسوم': d.fees,
                'المدة': d.duration_months,
                'تاريخ البداية': d.start_date,
                'الحالة': d.get_status_display(),
            })
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="diplomas.xlsx"'
        df.to_excel(response, index=False)
        logger.info(f'Diplomas exported by {request.user.username}')
        return response
    except Exception as e:
        logger.error(f'Error exporting diplomas: {str(e)}')
        messages.error(request, "حدث خطأ أثناء التصدير")
        return redirect('programs:diploma_list')


def export_diplomas_pdf(request):
    """تصدير الدبلومات لـ PDF"""
    from weasyprint import HTML
    from django.template.loader import render_to_string
    from django.conf import settings
    
    diplomas = Diploma.objects.all()
    logo_url = request.build_absolute_uri(settings.STATIC_URL + 'images/logo.png')
    
    context = {
        'diplomas': diplomas,
        'logo_url': logo_url,
        'user': request.user,
    }
    
    html_string = render_to_string('programs/diplomas_pdf_template.html', context)
    
    try:
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="diplomas_report.pdf"'
        logger.info(f'Diplomas PDF exported by {request.user.username}')
        return response
    except Exception as e:
        logger.error(f'Error generating PDF: {str(e)}')
        return HttpResponse(f"خطأ في إنشاء PDF: {str(e)}", status=500)


def export_courses_pdf(request):
    """تصدير الدورات لـ PDF"""
    courses = Course.objects.all()
    return get_pdf_response(
        request,
        'programs/courses_pdf_template.html',
        {'courses': courses, 'title': 'تقرير الدورات التدريبية'},
        'courses_report'
    )
