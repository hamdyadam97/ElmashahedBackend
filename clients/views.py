from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
import pandas as pd
import logging

from core.mixins import (
    EmployeeRequiredMixin, BranchManagerRequiredMixin,
    InstituteScopedMixin, SearchMixin, FilterMixin, SoftDeleteMixin
)
from core.utils import get_pdf_response
from institutes.models import Institute
from .models import Client

logger = logging.getLogger('edu_system')


class ClientListView(LoginRequiredMixin, InstituteScopedMixin, SearchMixin, FilterMixin, ListView):
    """قائمة العملاء"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    search_fields = ['full_name', 'national_id', 'phone']
    filter_fields = {'status': 'status'}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Client.Status.choices
        return context


class ClientCreateView(EmployeeRequiredMixin, CreateView):
    """إنشاء عميل جديد"""
    model = Client
    template_name = 'clients/client_form.html'
    fields = [
        'first_name', 'last_name', 'national_id', 'gender', 'birth_date',
        'phone', 'email', 'address', 'notes'
    ]
    success_url = reverse_lazy('clients:client_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_admin():
            context['institutes_list'] = Institute.objects.all()
        return context
    
    def form_valid(self, form):
        user = self.request.user
        
        if user.is_admin():
            selected_institute_id = self.request.POST.get('institute')
            if selected_institute_id:
                form.instance.institute_id = selected_institute_id
            else:
                form.add_error(None, "يجب اختيار المعهد التابع له العميل")
                return self.form_invalid(form)
        else:
            if user.is_employee():
                form.instance.institute = user.institute
            elif user.is_branch_manager():
                form.instance.institute = user.managed_institute
        
        form.instance.registered_by = user
        messages.success(self.request, f'تم إضافة العميل {form.instance.full_name} بنجاح')
        logger.info(f'Client {form.instance.full_name} created by {user.username}')
        return super().form_valid(form)


class ClientDetailView(LoginRequiredMixin, DetailView):
    """تفاصيل العميل"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        
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
        logger.info(f'Client {form.instance.full_name} updated by {self.request.user.username}')
        return super().form_valid(form)


class ClientDeleteView(BranchManagerRequiredMixin, SoftDeleteMixin, DeleteView):
    """حذف ناعم للعميل"""
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:client_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        client_name = self.object.full_name
        self.object.soft_delete()
        logger.warning(f'Client {client_name} archived by {request.user.username}')
        messages.success(request, f'تم نقل العميل "{client_name}" إلى الأرشيف بنجاح')
        return redirect(self.success_url)


# ==================== AJAX Views ====================

class ClientSearchView(LoginRequiredMixin, View):
    """البحث عن العملاء (AJAX)"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        user = request.user
        
        # فلترة حسب صلاحيات المستخدم
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
    """الحصول على عميل برقم الهوية (AJAX)"""
    
    def get(self, request):
        national_id = request.GET.get('national_id', '')
        user = request.user
        
        if not national_id:
            return JsonResponse({'found': False})
        
        # فلترة حسب صلاحيات المستخدم
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


# ==================== Import/Export Views ====================

def upload_clients(request):
    """استيراد العملاء من Excel/CSV"""
    if request.method != "POST" or not request.FILES.get('file'):
        return redirect('clients:client_list')
    
    uploaded_file = request.FILES['file']
    user = request.user
    
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        if 'birth_date' in df.columns:
            df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
        
        items_created = 0
        for _, row in df.iterrows():
            national_id = str(row.get('national_id', '')).strip()
            
            if not national_id or national_id == 'nan':
                continue
            
            # تحديد المعهد
            inst_id = row.get('institute')
            if not inst_id:
                if user.is_employee():
                    inst_id = user.institute_id
                elif user.is_branch_manager():
                    inst_id = user.managed_institute_id
            
            if not inst_id or not Institute.objects.filter(id=inst_id).exists():
                continue
            
            def clean_date(val):
                return val.date() if pd.notnull(val) and str(val) != 'NaT' else None
            
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
                    'registered_by': user,
                }
            )
            items_created += 1
        
        logger.info(f'{items_created} clients imported by {user.username}')
        messages.success(request, f"تم بنجاح معالجة {items_created} سجل للعملاء.")
    except Exception as e:
        logger.error(f'Error importing clients: {str(e)}')
        messages.error(request, f"حدث خطأ أثناء رفع العملاء: {str(e)}")
    
    return redirect('clients:client_list')


def export_clients_pdf(request):
    """تصدير العملاء PDF"""
    user = request.user
    
    if user.is_admin():
        clients = Client.objects.all()
    elif user.is_regional_manager():
        institutes = user.managed_institutes.all()
        clients = Client.objects.filter(institute__in=institutes)
    elif user.is_branch_manager():
        clients = Client.objects.filter(institute=user.managed_institute) if user.managed_institute else Client.objects.none()
    elif user.is_employee():
        clients = Client.objects.filter(institute=user.institute) if user.institute else Client.objects.none()
    else:
        clients = Client.objects.none()
    
    context = {
        'clients': clients,
        'title': 'سجل العملاء المسجلين',
    }
    return get_pdf_response(request, 'clients/clients_pdf_template.html', context, 'clients_report')


def export_clients_excel(request):
    """تصدير العملاء Excel"""
    user = request.user
    
    if user.is_admin():
        clients = Client.objects.all()
    elif user.is_regional_manager():
        institutes = user.managed_institutes.all()
        clients = Client.objects.filter(institute__in=institutes)
    elif user.is_branch_manager():
        clients = Client.objects.filter(institute=user.managed_institute) if user.managed_institute else Client.objects.none()
    elif user.is_employee():
        clients = Client.objects.filter(institute=user.institute) if user.institute else Client.objects.none()
    else:
        clients = Client.objects.none()
    
    df = pd.DataFrame(list(clients.values(
        'full_name', 'national_id', 'phone', 'email', 'status', 'institute__name', 'created_at'
    )))
    
    df.columns = ['الاسم الكامل', 'رقم الهوية', 'الهاتف', 'الإيميل', 'الحالة', 'المعهد', 'تاريخ التسجيل']
    df['تاريخ التسجيل'] = df['تاريخ التسجيل'].dt.date
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="clients_list.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='العملاء')
    
    logger.info(f'Clients exported by {user.username}')
    return response
