from django.views.generic import  ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from core.utils import get_pdf_response
from .models import  Diploma, ProgramRegistration
from accounts.views import AdminRequiredMixin, BranchManagerRequiredMixin, EmployeeRequiredMixin
import pandas as pd
from datetime import date
from django.contrib import messages
from django.shortcuts import redirect
from .models import Course, ProgramCategory
from institutes.models import Institute

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
        return super().form_valid(form)

class CategoryUpdateView(UpdateView):
    model = ProgramCategory
    template_name = 'programs/category_form.html'
    fields = ['name', 'type', 'description']
    success_url = reverse_lazy('programs:category_list')


class ProgramCategoryDeleteView(AdminRequiredMixin, DeleteView):
    """حذف ناعم للفئة وتأمين التوابع"""
    model = ProgramCategory
    template_name = 'programs/category_confirm_delete.html'
    success_url = reverse_lazy('programs:category_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # 1. الحذف الناعم للفئة نفسها
        self.object.soft_delete()

        # 2. الحذف الناعم لكل الكورسات والدبلومات التابعة لهذه الفئة
        # افترضنا هنا أن الـ related_name في الموديلات هو 'diplomas' و 'courses'
        if hasattr(self.object, 'diplomas'):
            self.object.diplomas.all().update(is_deleted=True)
        if hasattr(self.object, 'courses'):
            self.object.courses.all().update(is_deleted=True)

        messages.warning(request, f'تم أرشفة الفئة "{self.object.name}" وجميع البرامج التابعة لها.')
        return redirect(self.get_success_url())

    def delete(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# ==================== Diploma Views ====================

class DiplomaListView(LoginRequiredMixin, ListView):
    """قائمة الدبلومات"""
    model = Diploma
    template_name = 'programs/diploma_list.html'
    context_object_name = 'diplomas'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin():
            queryset = Diploma.objects.all()
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = Diploma.objects.filter(institute__in=institutes)
        elif user.is_branch_manager():
            queryset = Diploma.objects.filter(institute=user.managed_institute) if user.managed_institute else Diploma.objects.none()
        elif user.is_employee():
            queryset = Diploma.objects.filter(institute=user.institute) if user.institute else Diploma.objects.none()
        else:
            queryset = Diploma.objects.none()
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        
        # تصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # تصفية حسب المعهد
        institute = self.request.GET.get('institute')
        if institute:
            queryset = queryset.filter(institute_id=institute)
        
        return queryset.select_related('institute').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Diploma.Status.choices
        return context


class DiplomaCreateView(BranchManagerRequiredMixin, CreateView):
    model = Diploma
    template_name = 'programs/diploma_form.html'
    # 1. أضف 'institute' هنا ليظهر في الفورم
    fields = [
        'institute', 'name', 'code', 'description', 'category', 'duration_months',
        'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
        'fees', 'status'
    ]
    success_url = reverse_lazy('programs:diploma_list')

    # 2. إضافة قائمة المعاهد للـ Template (خاصة للأدمن)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # استيراد موديل المعهد هنا أو في أعلى الملف
        from institutes.models import Institute
        context['institutes'] = Institute.objects.all()
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # إذا كان المستخدم مدير فرع، نثبت المعهد ونخفي الاختيار أو نحدده له تلقائياً
        if hasattr(user, 'is_branch_manager') and user.is_branch_manager():
            form.instance.institute = user.managed_institute
            # اختياري: إزالة الحقل من الفورم لمدير الفرع لأنه محدد مسبقاً
            if 'institute' in form.fields:
                del form.fields['institute']

        return form

class DiplomaDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل الدبلومة"""
    model = Diploma
    template_name = 'programs/diploma_detail.html'
    context_object_name = 'diploma'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        diploma = self.get_object()
        
        # إحصائيات الدبلومة
        context['registrations_count'] = diploma.registrations.count()
        context['registrations'] = diploma.registrations.select_related(
            'client', 'registered_by'
        ).order_by('-created_at')[:20]
        
        return context


class DiplomaUpdateView(BranchManagerRequiredMixin, UpdateView):
    """تعديل الدبلومة"""
    model = Diploma
    template_name = 'programs/diploma_form.html'
    fields = [
        'institute','name', 'code', 'description', 'category', 'duration_months',
        'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
        'fees', 'status'
    ]
    
    def get_success_url(self):
        return reverse_lazy('programs:diploma_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الدبلومة بنجاح')
        return super().form_valid(form)


class DiplomaDeleteView(BranchManagerRequiredMixin, DeleteView):
    """حذف ناعم للدبلومة"""
    model = Diploma
    template_name = 'programs/diploma_confirm_delete.html'
    success_url = reverse_lazy('programs:diploma_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()  # استدعاء الدالة من BaseModel
        messages.success(request, f'تم نقل الدبلومة "{self.object.name}" للأرشيف.')
        return redirect(self.get_success_url())

    def delete(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)



# --- استيراد الدبلومات من Excel/CSV ---
def upload_diplomas(request):
    if request.method == "POST" and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        try:
            # قراءة الملف
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)

            # حذف المسافات الزائدة من أسماء الأعمدة للتأكد
            df.columns = df.columns.str.strip()
            # تنظيف أسماء الأعمدة

            # ✅ تحويل أعمدة التاريخ مرة واحدة
            date_columns = [
                'start_date',
                'end_date',
                'registration_start_date',
                'registration_end_date'
            ]

            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            items_created = 0
            for _, row in df.iterrows():
                # الحصول على الـ ID من العمود institute_id الموجود في ملفك
                inst_id = row.get('institute')
                cat_id = row.get('category')
                print(inst_id)
                print('ssssssssssssss')
                print(cat_id)
                # التحقق من وجود المعهد في قاعدة البيانات أولاً
                if not Institute.objects.filter(id=inst_id).exists():
                    print('sssssssssssssssssssssssssssssssss')
                    continue  # لو المعهد مش موجود في قاعدة البيانات هيتخطى الصف

                if not ProgramCategory.objects.filter(id=cat_id).exists():
                    continue  # لو المعهد مش موجود في قاعدة البيانات هيتخطى الصف
                # الحفظ أو التحديث
                Diploma.objects.update_or_create(
                    code=row['code'],
                    defaults={
                        'name': row['name'],
                        'description': row.get('description', ''),  # حسب صورة الملف المقطوعة
                        'institute_id': inst_id,  # الربط المباشر بالـ ID
                        'category_id': row.get('category'),
                        'duration_months': row.get('duration_', 24),
                        'fees': row.get('fees', 0.00),
                        'start_date': row['start_date'],
                        'end_date': row['end_date'],
                        'registration_start_date': row.get('registration_start_date'),
                        'registration_end_date': row.get('registration_end_date'),
                        'status': row.get('status', 'active'),
                    }
                )
                items_created += 1

            if items_created > 0:
                messages.success(request, f"تم رفع {items_created} دبلومة بنجاح.")
            else:
                messages.warning(request,
                                 "لم يتم رفع أي بيانات. تأكد من أن أرقام الـ IDs للمعاهد في الملف صحيحة وموجودة في النظام.")

        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء المعالجة: {str(e)}")

    return redirect('programs:diploma_list')

# --- تصدير الدبلومات لـ Excel ---
def export_diplomas_excel(request):
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
    return response


# --- تصدير الدبلومات لـ PDF ---
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
import os


def export_diplomas_pdf(request):
    diplomas = Diploma.objects.all()

    # تجهيز رابط اللوجو (هنجيب الرابط الكامل عشان WeasyPrint يشوفه)
    # تأكد إن الصورة موجودة في static/images/logo.png
    logo_url = request.build_absolute_uri(settings.STATIC_URL + 'images/logo.png')

    # رندر الـ HTML ببيانات واضحة
    context = {
        'diplomas': diplomas,
        'logo_url': logo_url,
        'user': request.user,
    }

    html_string = render_to_string('programs/diplomas_pdf_template.html', context)

    try:
        # تحويل لـ PDF
        # base_url مهم جداً عشان التنسيقات (CSS) والصور تظهر
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="diplomas_report.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"خطأ في إنشاء ملف PDF: {str(e)}", status=500)
# ==================== Course Views ====================

class CourseListView(LoginRequiredMixin, ListView):
    """قائمة الدورات"""
    model = Course
    template_name = 'programs/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin():
            queryset = Course.objects.all()
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = Course.objects.filter(institute__in=institutes)
        elif user.is_branch_manager():
            queryset = Course.objects.filter(institute=user.managed_institute) if user.managed_institute else Course.objects.none()
        elif user.is_employee():
            queryset = Course.objects.filter(institute=user.institute) if user.institute else Course.objects.none()
        else:
            queryset = Course.objects.none()
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        
        # تصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('institute').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Course.Status.choices
        return context


class CourseCreateView(BranchManagerRequiredMixin, CreateView):
    """إنشاء دورة جديدة"""
    model = Course
    template_name = 'programs/course_form.html'
    fields = [
        'institute','name', 'code', 'description', 'category', 'duration_months',
        'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
        'fees', 'status'
    ]
    success_url = reverse_lazy('programs:course_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        # تحديد المعهد حسب المستخدم
        if user.is_branch_manager():
            form.instance.institute = user.managed_institute
        elif user.is_employee():
            form.instance.institute = user.institute
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, f'تم إنشاء الدورة {form.instance.name} بنجاح')
        return super().form_valid(form)


class CourseDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل الدورة"""
    model = Course
    template_name = 'programs/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # إحصائيات الدورة
        context['registrations_count'] = course.registrations.count()
        context['registrations'] = course.registrations.select_related(
            'client', 'registered_by'
        ).order_by('-created_at')[:20]
        
        return context


class CourseUpdateView(BranchManagerRequiredMixin, UpdateView):
    """تعديل الدورة"""
    model = Course
    template_name = 'programs/course_form.html'
    fields = [
        'institute','name', 'code', 'description', 'category', 'duration_months',
        'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
        'fees', 'status'
    ]
    
    def get_success_url(self):
        return reverse_lazy('programs:course_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الدورة بنجاح')
        return super().form_valid(form)



class CourseDeleteView(BranchManagerRequiredMixin, DeleteView):
    """حذف ناعم للدورة"""
    model = Course
    template_name = 'programs/course_confirm_delete.html'
    success_url = reverse_lazy('programs:course_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(request, f'تم نقل الدورة "{self.object.name}" للأرشيف.')
        return redirect(self.get_success_url())

    def delete(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)





def upload_courses(request):
    if request.method == "POST" and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        try:
            # 1. قراءة الملف
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)

            # 2. تنظيف أسماء الأعمدة (تحويلها لنصوص ثم تنظيفها ثم حروف صغيرة)
            df.columns = [str(col).strip().lower() for col in df.columns]

            # 3. تحويل أعمدة التاريخ (تأكد أن الأسماء في الإكسيل تطابق هذه الأسماء)
            date_cols = ['start_date', 'end_date', 'registration_start_date', 'registration_end_date']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            items_created = 0
            for index, row in df.iterrows():
                # جلب البيانات (استخدمنا get لأن الأسماء أصبحت صغيرة lower)
                inst_id = row.get('institute')
                cat_id = row.get('category')
                code = str(row.get('code', '')).strip()

                if not Institute.objects.filter(id=inst_id).exists():
                    continue

                def clean_date(val, fallback):
                    if pd.notnull(val) and str(val) != 'NaT':
                        return val.date()
                    return fallback

                s_date = clean_date(row.get('start_date'), date.today())
                e_date = clean_date(row.get('end_date'), s_date)
                reg_e = clean_date(row.get('registration_end_date'), e_date)
                reg_s = clean_date(row.get('registration_start_date'), s_date)

                Course.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': row.get('name'),
                        'description': row.get('description', ''),
                        'institute_id': inst_id,
                        'category_id': cat_id,
                        'duration_months': row.get('duration_', 6),
                        'fees': row.get('fees', 0.00),
                        'start_date': s_date,
                        'end_date': e_date,
                        'registration_start_date': reg_s,
                        'registration_end_date': reg_e,
                        'status': row.get('status', 'active'),
                    }
                )
                items_created += 1

            messages.success(request, f"تمت العملية بنجاح. تم رفع {items_created} كورس.")

        except Exception as e:
            messages.error(request, f"حدث خطأ غير متوقع: {str(e)}")

    return redirect('programs:course_list')


def export_courses_pdf(request):
    courses = Course.objects.all()
    return get_pdf_response(request, 'programs/courses_pdf_template.html',
                          {'courses': courses, 'title': 'تقرير الدورات التدريبية'}, 'courses_report')
# ==================== Registration Views ====================

class RegistrationListView(LoginRequiredMixin, ListView):
    """قائمة التسجيلات"""
    model = ProgramRegistration
    template_name = 'programs/registration_list.html'
    context_object_name = 'registrations'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin():
            queryset = ProgramRegistration.objects.all()
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = ProgramRegistration.objects.filter(
                Q(diploma__institute__in=institutes) |
                Q(course__institute__in=institutes)
            )
        elif user.is_branch_manager():
            institute = user.managed_institute
            queryset = ProgramRegistration.objects.filter(
                Q(diploma__institute=institute) |
                Q(course__institute=institute)
            ) if institute else ProgramRegistration.objects.none()
        elif user.is_employee():
            institute = user.institute
            queryset = ProgramRegistration.objects.filter(
                Q(diploma__institute=institute) |
                Q(course__institute=institute)
            ) if institute else ProgramRegistration.objects.none()
        else:
            queryset = ProgramRegistration.objects.none()
        
        # تصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('client', 'diploma', 'course', 'registered_by').order_by('-created_at')


class RegistrationCreateView(EmployeeRequiredMixin, CreateView):
    """إنشاء تسجيل جديد"""
    model = ProgramRegistration
    template_name = 'programs/registration_form.html'
    fields = ['client', 'diploma', 'course', 'status', 'notes']
    success_url = reverse_lazy('programs:registration_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        # تصفية الخيارات حسب معهد المستخدم
        if user.institute:
            form.fields['diploma'].queryset = user.institute.diplomas.filter(status='active')
            form.fields['course'].queryset = user.institute.courses.filter(status='active')
        
        return form
    
    def form_valid(self, form):
        form.instance.registered_by = self.request.user
        messages.success(self.request, 'تم تسجيل العميل بنجاح')
        return super().form_valid(form)


class RegistrationDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل التسجيل"""
    model = ProgramRegistration
    template_name = 'programs/registration_detail.html'
    context_object_name = 'registration'




