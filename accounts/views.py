from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import User
from institutes.models import Institute
from permissions.models import PermissionSlip
from clients.models import Client
from programs.models import ProgramRegistration
from core.mixins import (
    AdminRequiredMixin, RegionalManagerRequiredMixin,
    BranchManagerRequiredMixin, EmployeeRequiredMixin,
    SearchMixin, FilterMixin
)

logger = logging.getLogger('edu_system')


class CustomLoginView(auth_views.LoginView):
    """صفحة تسجيل الدخول"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        logger.info(f'User {form.get_user().username} logged in')
        return super().form_valid(form)


class CustomLogoutView(View):
    """تسجيل الخروج - يعمل مع GET و POST"""
    def get(self, request, *args, **kwargs):
        return self._logout(request)
    
    def post(self, request, *args, **kwargs):
        return self._logout(request)
    
    def _logout(self, request):
        if request.user.is_authenticated:
            logger.info(f'User {request.user.username} logged out')
        logout(request)
        messages.success(request, 'تم تسجيل الخروج بنجاح')
        return redirect('accounts:login')


class DashboardView(LoginRequiredMixin, TemplateView):
    """لوحة التحكم الرئيسية"""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            if user.is_admin():
                context.update(self._get_admin_context())
            elif user.is_regional_manager():
                context.update(self._get_regional_manager_context(user))
            elif user.is_branch_manager():
                context.update(self._get_branch_manager_context(user))
            elif user.is_employee():
                context.update(self._get_employee_context(user))
        except Exception as e:
            logger.error(f'Error loading dashboard for user {user.username}: {str(e)}')
            messages.error(self.request, 'حدث خطأ في تحميل لوحة التحكم')
        
        return context
    
    def _get_admin_context(self):
        """إحصائيات Admin"""
        return {
            'total_institutes': Institute.objects.count(),
            'total_users': User.objects.filter(is_active=True).count(),
            'total_clients': Client.objects.count(),
            'total_permissions': PermissionSlip.objects.count(),
            'recent_permissions': PermissionSlip.objects.select_related(
                'client', 'institute'
            ).order_by('-created_at')[:10],
        }
    
    def _get_regional_manager_context(self, user):
        """إحصائيات المدير الإقليمي"""
        institutes = user.managed_institutes.all()
        return {
            'managed_institutes': institutes,
            'total_clients': Client.objects.filter(institute__in=institutes).count(),
            'total_permissions': PermissionSlip.objects.filter(
                institute__in=institutes
            ).count(),
            'recent_permissions': PermissionSlip.objects.filter(
                institute__in=institutes
            ).select_related('client', 'institute').order_by('-created_at')[:10],
        }
    
    def _get_branch_manager_context(self, user):
        """إحصائيات مدير الفرع"""
        institute = user.managed_institute
        if not institute:
            return {}
        return {
            'institute': institute,
            'total_clients': Client.objects.filter(institute=institute).count(),
            'total_permissions': PermissionSlip.objects.filter(
                institute=institute
            ).count(),
            'recent_permissions': PermissionSlip.objects.filter(
                institute=institute
            ).select_related('client').order_by('-created_at')[:10],
            'employees': User.objects.filter(
                institute=institute, role='employee'
            ),
        }
    
    def _get_employee_context(self, user):
        """إحصائيات الموظف"""
        institute = user.institute
        if not institute:
            return {}
        return {
            'institute': institute,
            'my_permissions': PermissionSlip.objects.filter(
                issued_by=user
            ).count(),
            'my_clients': Client.objects.filter(
                registered_by=user
            ).count(),
            'recent_permissions': PermissionSlip.objects.filter(
                issued_by=user
            ).select_related('client').order_by('-created_at')[:5],
        }


# ==================== User Management Views ====================

class UserListView(AdminRequiredMixin, SearchMixin, FilterMixin, ListView):
    """قائمة المستخدمين"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    search_fields = ['username', 'first_name', 'last_name', 'email']
    filter_fields = {'role': 'role'}
    
    def get_queryset(self):
        return super().get_queryset().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = User.Role.choices
        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    """إنشاء مستخدم جديد"""
    model = User
    template_name = 'accounts/user_form.html'
    fields = [
        'username', 'first_name', 'last_name', 'email', 'phone', 'address',
        'role', 'institute', 'managed_institute', 'managed_institutes',
        'is_active', 'password'
    ]
    success_url = reverse_lazy('accounts:user_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        form.save_m2m()  # Save many-to-many relationships
        messages.success(self.request, f'تم إنشاء المستخدم {user.username} بنجاح')
        logger.info(f'User {user.username} created by {self.request.user.username}')
        return redirect(self.success_url)


class UserDetailView(AdminRequiredMixin, DetailView):
    """تفاصيل المستخدم"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        context['permissions_count'] = PermissionSlip.objects.filter(
            issued_by=user
        ).count()
        context['clients_count'] = Client.objects.filter(
            registered_by=user
        ).count()
        
        return context


class UserUpdateView(AdminRequiredMixin, UpdateView):
    """تعديل المستخدم"""
    model = User
    template_name = 'accounts/user_form.html'
    fields = [
        'username', 'first_name', 'last_name', 'email', 'phone', 'address',
        'role', 'institute', 'managed_institute', 'managed_institutes',
        'is_active'
    ]
    success_url = reverse_lazy('accounts:user_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث المستخدم بنجاح')
        logger.info(f'User {form.instance.username} updated by {self.request.user.username}')
        return super().form_valid(form)


class UserDeleteView(AdminRequiredMixin, DeleteView):
    """حذف المستخدم"""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        logger.warning(f'User {user.username} deleted by {request.user.username}')
        messages.success(request, 'تم حذف المستخدم بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Profile Views ====================

class ProfileView(LoginRequiredMixin, TemplateView):
    """الملف الشخصي - عرض شامل للمستخدم"""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # إحصائيات أساسية
        context['permissions_count'] = PermissionSlip.objects.filter(
            issued_by=user
        ).count()
        context['clients_count'] = Client.objects.filter(
            registered_by=user
        ).count()
        
        # إحصائيات شهرية
        today = timezone.now()
        current_month = today.month
        current_year = today.year
        
        context['monthly_permissions'] = PermissionSlip.objects.filter(
            issued_by=user,
            created_at__year=current_year,
            created_at__month=current_month
        ).count()
        
        context['monthly_clients'] = Client.objects.filter(
            registered_by=user,
            created_at__year=current_year,
            created_at__month=current_month
        ).count()
        
        # آخر الأنشطة
        context['recent_permissions'] = PermissionSlip.objects.filter(
            issued_by=user
        ).select_related('client', 'institute').order_by('-created_at')[:10]
        
        context['recent_clients'] = Client.objects.filter(
            registered_by=user
        ).select_related('institute').order_by('-created_at')[:10]
        
        # بيانات المعهد
        if user.institute:
            context['user_institute'] = user.institute
        elif user.managed_institute:
            context['user_institute'] = user.managed_institute
        
        # إحصائيات السنة
        context['yearly_stats'] = self._get_yearly_stats(user)
        
        return context
    
    def _get_yearly_stats(self, user):
        """إحصائيات السنة الحالية شهراً بشهر"""
        current_year = timezone.now().year
        stats = []
        
        for month in range(1, 13):
            permissions = PermissionSlip.objects.filter(
                issued_by=user,
                created_at__year=current_year,
                created_at__month=month
            ).count()
            clients = Client.objects.filter(
                registered_by=user,
                created_at__year=current_year,
                created_at__month=month
            ).count()
            stats.append({
                'month': month,
                'permissions': permissions,
                'clients': clients
            })
        
        return stats


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل الملف الشخصي"""
    model = User
    template_name = 'accounts/profile_edit.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'address']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        """التأكد من أن المستخدم يعدل بياناته فقط"""
        return self.request.user
    
    def form_valid(self, form):
        """حفظ البيانات مع التحقق"""
        # التأكد من عدم تعديل حقول محظورة
        if 'role' in form.changed_data or 'username' in form.changed_data:
            messages.error(self.request, 'لا يمكن تعديل هذه البيانات')
            return self.form_invalid(form)
        
        messages.success(self.request, '✅ تم تحديث الملف الشخصي بنجاح')
        logger.info(f'User {form.instance.username} updated their profile. Changed fields: {form.changed_data}')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """معالجة الأخطاء"""
        messages.error(self.request, '❌ يرجى تصحيح الأخطاء أدناه')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


# ==================== Reports Views ====================

class ReportsView(LoginRequiredMixin, TemplateView):
    """صفحة التقارير"""
    template_name = 'accounts/reports.html'


class EmployeeReportView(LoginRequiredMixin, TemplateView):
    """تقرير الموظف الشخصي"""
    template_name = 'accounts/employee_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        try:
            permissions = PermissionSlip.objects.filter(
                issued_by=user,
                created_at__year=year,
                created_at__month=month
            )
            
            context['permissions_count'] = permissions.count()
            context['permissions'] = permissions.select_related('client', 'diploma', 'course')
            context['month'] = month
            context['year'] = year
        except Exception as e:
            logger.error(f'Error generating employee report for {user.username}: {str(e)}')
            messages.error(self.request, 'حدث خطأ في توليد التقرير')
        
        return context


class BranchReportView(BranchManagerRequiredMixin, TemplateView):
    """تقرير مدير الفرع"""
    template_name = 'accounts/branch_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        institute = user.managed_institute
        if not institute:
            return context
        
        try:
            context['institute'] = institute
            context['total_clients'] = Client.objects.filter(institute=institute).count()
            context['total_permissions'] = PermissionSlip.objects.filter(
                institute=institute,
                created_at__year=year,
                created_at__month=month
            ).count()
            
            # أداء الموظفين
            employees = User.objects.filter(institute=institute, role='employee')
            context['employees_performance'] = []
            for emp in employees:
                emp_permissions = PermissionSlip.objects.filter(
                    issued_by=emp,
                    created_at__year=year,
                    created_at__month=month
                ).count()
                context['employees_performance'].append({
                    'employee': emp,
                    'permissions_count': emp_permissions
                })
            
            context['month'] = month
            context['year'] = year
        except Exception as e:
            logger.error(f'Error generating branch report: {str(e)}')
            messages.error(self.request, 'حدث خطأ في توليد التقرير')
        
        return context


class RegionalReportView(RegionalManagerRequiredMixin, TemplateView):
    """تقرير المدير الإقليمي"""
    template_name = 'accounts/regional_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        try:
            institutes = user.managed_institutes.all()
            context['institutes'] = institutes
            
            context['institutes_reports'] = []
            for institute in institutes:
                report = {
                    'institute': institute,
                    'clients_count': Client.objects.filter(institute=institute).count(),
                    'permissions_count': PermissionSlip.objects.filter(
                        institute=institute,
                        created_at__year=year,
                        created_at__month=month
                    ).count()
                }
                context['institutes_reports'].append(report)
            
            context['month'] = month
            context['year'] = year
        except Exception as e:
            logger.error(f'Error generating regional report: {str(e)}')
            messages.error(self.request, 'حدث خطأ في توليد التقرير')
        
        return context


class AdminReportView(AdminRequiredMixin, TemplateView):
    """تقرير الأدمن الشامل"""
    template_name = 'accounts/admin_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        try:
            context['total_institutes'] = Institute.objects.count()
            context['total_users'] = User.objects.filter(is_active=True).count()
            context['total_clients'] = Client.objects.count()
            context['total_permissions'] = PermissionSlip.objects.filter(
                created_at__year=year,
                created_at__month=month
            ).count()
            
            institutes = Institute.objects.all()
            context['institutes_reports'] = []
            for institute in institutes:
                report = {
                    'institute': institute,
                    'clients_count': Client.objects.filter(institute=institute).count(),
                    'permissions_count': PermissionSlip.objects.filter(
                        institute=institute,
                        created_at__year=year,
                        created_at__month=month
                    ).count(),
                    'employees_count': User.objects.filter(institute=institute, role='employee').count()
                }
                context['institutes_reports'].append(report)
            
            context['month'] = month
            context['year'] = year
        except Exception as e:
            logger.error(f'Error generating admin report: {str(e)}')
            messages.error(self.request, 'حدث خطأ في توليد التقرير')
        
        return context
