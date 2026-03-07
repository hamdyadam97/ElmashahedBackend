from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from institutes.models import Institute
from accounts.views import EmployeeRequiredMixin, BranchManagerRequiredMixin
import pandas as pd
from django.http import HttpResponse
from .models import Client
from core.utils import get_pdf_response  # الدالة المساعدة التي أنشأناها سابقاً



class ClientListView(LoginRequiredMixin, ListView):
    """قائمة العملاء"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin():
            queryset = Client.objects.all()
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = Client.objects.filter(institute__in=institutes)
        elif user.is_branch_manager():
            queryset = Client.objects.filter(institute=user.managed_institute) if user.managed_institute else Client.objects.none()
        elif user.is_employee():
            queryset = Client.objects.filter(institute=user.institute) if user.institute else Client.objects.none()
        else:
            queryset = Client.objects.none()
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(national_id__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # تصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related('institute', 'registered_by').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Client.Status.choices
        return context


class ClientCreateView(EmployeeRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/client_form.html'
    fields = [
        'first_name', 'last_name', 'national_id', 'gender', 'birth_date',
        'phone', 'email', 'address', 'notes'
    ]
    success_url = reverse_lazy('clients:client_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # تمرير قائمة المعاهد فقط إذا كان المستخدم Admin ليختار منها
        if self.request.user.is_admin():
            from institutes.models import Institute
            context['institutes_list'] = Institute.objects.all()
        return context

    def form_valid(self, form):
        user = self.request.user

        if user.is_admin():
            # إذا كان أدمن، نأخذ المعهد من القيمة المختارة في الفورم
            selected_institute_id = self.request.POST.get('institute')
            if selected_institute_id:
                form.instance.institute_id = selected_institute_id
            else:
                # إذا لم يختر الأدمن معهداً، نعرض خطأ بدلاً من كراش النظام
                form.add_error(None, "يجب اختيار المعهد التابع له العميل")
                return self.form_invalid(form)
        else:
            # للموظفين، نحدد المعهد تلقائياً من بياناتهم
            if user.is_employee():
                form.instance.institute = user.institute
            elif user.is_branch_manager():
                form.instance.institute = user.managed_institute

        form.instance.registered_by = user
        messages.success(self.request, f'تم إضافة العميل {form.instance.full_name} بنجاح')
        return super().form_valid(form)

class ClientDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل العميل"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        
        # إحصائيات العميل
        context['registrations'] = client.registrations.select_related(
            'diploma', 'course'
        ).order_by('-created_at')
        context['permissions'] = client.permissions.select_related(
            'diploma', 'course', 'issued_by'
        ).order_by('-created_at')[:10]
        
        return context


class ClientUpdateView(EmployeeRequiredMixin, UpdateView):
    """تعديل العميل"""
    model = Client
    template_name = 'clients/client_form.html'
    fields = [
        'first_name', 'last_name', 'national_id', 'gender', 'birth_date',
        'phone', 'email', 'address', 'status', 'notes'
    ]
    
    def get_success_url(self):
        return reverse_lazy('clients:client_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث بيانات العميل بنجاح')
        return super().form_valid(form)


class ClientDeleteView(BranchManagerRequiredMixin, DeleteView):
    """حذف ناعم للعميل"""
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:client_list')

    def post(self, request, *args, **kwargs):
        # جلب العميل
        self.object = self.get_object()
        # تنفيذ الحذف الناعم (الدالة التي وضعناها في الـ BaseModel)
        self.object.soft_delete()

        messages.success(request, f'تم نقل العميل "{self.object.full_name}" إلى الأرشيف بنجاح')
        return redirect(self.get_success_url())

    # إلغاء دالة delete الأصلية لضمان عدم المسح الفعلي أبداً
    def delete(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ClientSearchView(LoginRequiredMixin, View):
    """البحث عن العملاء"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        user = request.user
        
        if user.is_admin():
            queryset = Client.objects.all()
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = Client.objects.filter(institute__in=institutes)
        elif user.is_branch_manager():
            queryset = Client.objects.filter(institute=user.managed_institute) if user.managed_institute else Client.objects.none()
        elif user.is_employee():
            queryset = Client.objects.filter(institute=user.institute) if user.institute else Client.objects.none()
        else:
            queryset = Client.objects.none()
        
        if query:
            queryset = queryset.filter(
                Q(full_name__icontains=query) |
                Q(national_id__icontains=query) |
                Q(phone__icontains=query)
            )[:10]
        else:
            queryset = queryset.none()
        
        results = [{
            'id': c.id,
            'full_name': c.full_name,
            'national_id': c.national_id,
            'phone': c.phone,
            'institute': c.institute.name if c.institute else '-'
        } for c in queryset]
        
        return JsonResponse({'results': results})


class GetClientByNationalIdView(LoginRequiredMixin, View):
    """الحصول على عميل برقم الهوية"""
    
    def get(self, request):
        national_id = request.GET.get('national_id', '')
        user = request.user
        
        if not national_id:
            return JsonResponse({'found': False})
        
        if user.is_admin():
            queryset = Client.objects.all()
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = Client.objects.filter(institute__in=institutes)
        elif user.is_branch_manager():
            queryset = Client.objects.filter(institute=user.managed_institute) if user.managed_institute else Client.objects.none()
        elif user.is_employee():
            queryset = Client.objects.filter(institute=user.institute) if user.institute else Client.objects.none()
        else:
            queryset = Client.objects.none()
        
        try:
            client = queryset.get(national_id=national_id)
            return JsonResponse({
                'found': True,
                'client': {
                    'id': client.id,
                    'full_name': client.full_name,
                    'national_id': client.national_id,
                    'phone': client.phone,
                    'email': client.email,
                    'birth_date': client.birth_date.strftime('%Y-%m-%d') if client.birth_date else None,
                    'gender': client.gender,
                    'address': client.address,
                    'institute_id': client.institute_id
                }
            })
        except Client.DoesNotExist:
            return JsonResponse({'found': False})





def upload_clients(request):
    """دالة استيراد العملاء من ملف Excel/CSV"""
    if request.method == "POST" and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        user = request.user

        try:
            # 1. قراءة الملف وتنظيف أسماء الأعمدة
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df.columns = [str(col).strip().lower() for col in df.columns]

            # 2. تحويل أعمدة التاريخ (تاريخ الميلاد)
            if 'birth_date' in df.columns:
                df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')

            items_created = 0
            for index, row in df.iterrows():
                national_id = str(row.get('national_id', '')).strip()

                # تخطي الصف لو رقم الهوية فارغ
                if not national_id or national_id == 'nan':
                    continue

                # تحديد المعهد (إما من الإكسيل أو من معهد الموظف الحالي)
                inst_id = row.get('institute')
                if not inst_id:
                    if user.is_employee():
                        inst_id = user.institute_id
                    elif user.is_branch_manager():
                        inst_id = user.managed_institute_id

                # التأكد من وجود المعهد
                if not inst_id or not Institute.objects.filter(id=inst_id).exists():
                    continue

                def clean_date(val):
                    return val.date() if pd.notnull(val) and str(val) != 'NaT' else None

                # 3. الحفظ أو التحديث بناءً على رقم الهوية (National ID)
                Client.objects.update_or_create(
                    national_id=national_id,
                    defaults={
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'gender': row.get('gender', 'male'),
                        'birth_date': clean_date(row.get('birth_date')),
                        'phone': str(row.get('phone', '')).strip(),
                        'email': row.get('email', ''),
                        'address': row.get('address', ''),
                        'notes': row.get('notes', ''),
                        'status': row.get('status', 'active'),
                        'institute_id': inst_id,
                        'registered_by': user,  # الموظف اللي بيرفع الملف حالياً
                    }
                )
                items_created += 1

            messages.success(request, f"تم بنجاح معالجة {items_created} سجل للعملاء.")

        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء رفع العملاء: {str(e)}")

    return redirect('clients:client_list')



# --- تصدير العملاء PDF ---
def export_clients_pdf(request):
    # جلب نفس الداتا اللي الموظف مسموح له يشوفها (حسب الـ Queryset في ListView)
    # هنا مثال عام ويمكنك تخصيصه حسب صلاحيات المستخدم
    clients = Client.objects.all()

    context = {
        'clients': clients,
        'title': 'سجل العملاء المسجلين',
    }
    return get_pdf_response(request, 'clients/clients_pdf_template.html', context, 'clients_report')


# --- تصدير العملاء Excel ---
def export_clients_excel(request):
    clients = Client.objects.all().values(
        'full_name', 'national_id', 'phone', 'email', 'status', 'institute__name', 'created_at'
    )

    df = pd.DataFrame(list(clients))

    # تحسين أسماء الأعمدة في ملف الإكسيل
    df.columns = ['الاسم الكامل', 'رقم الهوية', 'الهاتف', 'الإيميل', 'الحالة', 'المعهد', 'تاريخ التسجيل']

    # إزالة التوقيت من تاريخ التسجيل ليظهر التاريخ فقط
    df['تاريخ التسجيل'] = df['تاريخ التسجيل'].dt.date

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="clients_list.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='العملاء')

    return response