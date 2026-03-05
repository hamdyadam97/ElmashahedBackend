from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import User
from institutes.models import Institute
from permissions.models import PermissionSlip
from clients.models import Client
from programs.models import ProgramRegistration


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin للتحقق من أن المستخدم Admin"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()


class RegionalManagerRequiredMixin(UserPassesTestMixin):
    """Mixin للتحقق من أن المستخدم مدير إقليمي أو أعلى"""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_admin() or user.is_regional_manager())


class BranchManagerRequiredMixin(UserPassesTestMixin):
    """Mixin للتحقق من أن المستخدم مدير فرع أو أعلى"""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_admin() or user.is_regional_manager() or user.is_branch_manager()
        )


class EmployeeRequiredMixin(UserPassesTestMixin):
    """Mixin للتحقق من أن المستخدم موظف أو أعلى"""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_admin() or user.is_regional_manager() or 
            user.is_branch_manager() or user.is_employee()
        )


class CustomLoginView(auth_views.LoginView):
    """صفحة تسجيل الدخول"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class DashboardView(LoginRequiredMixin, TemplateView):
    """لوحة التحكم الرئيسية"""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # إحصائيات عامة حسب دور المستخدم
        if user.is_admin():
            context['total_institutes'] = Institute.objects.count()
            context['total_users'] = User.objects.filter(is_active=True).count()
            context['total_clients'] = Client.objects.count()
            context['total_permissions'] = PermissionSlip.objects.count()
            context['recent_permissions'] = PermissionSlip.objects.select_related(
                'client', 'institute'
            ).order_by('-created_at')[:10]
            
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            context['managed_institutes'] = institutes
            context['total_clients'] = Client.objects.filter(institute__in=institutes).count()
            context['total_permissions'] = PermissionSlip.objects.filter(
                institute__in=institutes
            ).count()
            context['recent_permissions'] = PermissionSlip.objects.filter(
                institute__in=institutes
            ).select_related('client', 'institute').order_by('-created_at')[:10]
            
        elif user.is_branch_manager():
            institute = user.managed_institute
            if institute:
                context['institute'] = institute
                context['total_clients'] = Client.objects.filter(institute=institute).count()
                context['total_permissions'] = PermissionSlip.objects.filter(
                    institute=institute
                ).count()
                context['recent_permissions'] = PermissionSlip.objects.filter(
                    institute=institute
                ).select_related('client').order_by('-created_at')[:10]
                context['employees'] = User.objects.filter(
                    institute=institute, role='employee'
                )
                
        elif user.is_employee():
            institute = user.institute
            if institute:
                context['institute'] = institute
                context['my_permissions'] = PermissionSlip.objects.filter(
                    issued_by=user
                ).count()
                context['my_clients'] = Client.objects.filter(
                    registered_by=user
                ).count()
                context['recent_permissions'] = PermissionSlip.objects.filter(
                    issued_by=user
                ).select_related('client').order_by('-created_at')[:5]
        
        return context


# ==================== User Management Views ====================

class UserListView(AdminRequiredMixin, ListView):
    """قائمة المستخدمين"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        # تصفية حسب الدور
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset.order_by('-created_at')
    
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
        messages.success(self.request, f'تم إنشاء المستخدم {user.username} بنجاح')
        return super().form_valid(form)


class UserDetailView(AdminRequiredMixin, DetailView):
    """تفاصيل المستخدم"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # إحصائيات المستخدم
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
        return super().form_valid(form)


class UserDeleteView(AdminRequiredMixin, DeleteView):
    """حذف المستخدم"""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف المستخدم بنجاح')
        return super().delete(request, *args, **kwargs)


# ==================== Profile Views ====================

class ProfileView(LoginRequiredMixin, TemplateView):
    """الملف الشخصي"""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # إحصائيات المستخدم
        context['permissions_count'] = PermissionSlip.objects.filter(
            issued_by=user
        ).count()
        context['clients_count'] = Client.objects.filter(
            registered_by=user
        ).count()
        
        # آخر الأذونات
        context['recent_permissions'] = PermissionSlip.objects.filter(
            issued_by=user
        ).select_related('client').order_by('-created_at')[:5]
        
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل الملف الشخصي"""
    model = User
    template_name = 'accounts/profile_edit.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'address']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الملف الشخصي بنجاح')
        return super().form_valid(form)


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
        
        # الفترة الزمنية
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        # إحصائيات الأذونات
        permissions = PermissionSlip.objects.filter(
            issued_by=user,
            created_at__year=year,
            created_at__month=month
        )
        
        context['permissions_count'] = permissions.count()
        context['permissions'] = permissions.select_related('client', 'diploma', 'course')
        context['month'] = month
        context['year'] = year
        
        return context


class BranchReportView(BranchManagerRequiredMixin, TemplateView):
    """تقرير مدير الفرع"""
    template_name = 'accounts/branch_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # الفترة الزمنية
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        institute = user.managed_institute
        if institute:
            context['institute'] = institute
            
            # إحصائيات المعهد
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
        
        return context


class RegionalReportView(RegionalManagerRequiredMixin, TemplateView):
    """تقرير المدير الإقليمي"""
    template_name = 'accounts/regional_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # الفترة الزمنية
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        institutes = user.managed_institutes.all()
        context['institutes'] = institutes
        
        # تقارير مجمعة
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
        
        return context


class AdminReportView(AdminRequiredMixin, TemplateView):
    """تقرير الأدمن الشامل"""
    template_name = 'accounts/admin_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # الفترة الزمنية
        month = self.request.GET.get('month', timezone.now().month)
        year = self.request.GET.get('year', timezone.now().year)
        
        # إحصائيات عامة
        context['total_institutes'] = Institute.objects.count()
        context['total_users'] = User.objects.filter(is_active=True).count()
        context['total_clients'] = Client.objects.count()
        context['total_permissions'] = PermissionSlip.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count()
        
        # تقارير المعاهد
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
        
        return context
