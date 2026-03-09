from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """نموذج المستخدم المخصص مع الأدوار المختلفة"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Admin / CEO')
        REGIONAL_MANAGER = 'regional_manager', _('Regional Manager')
        BRANCH_MANAGER = 'branch_manager', _('Branch Manager')
        EMPLOYEE = 'employee', _('Employee')
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name=_('Role')
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'))
    address = models.TextField(blank=True, verbose_name=_('Address'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    # العلاقات
    managed_institutes = models.ManyToManyField(
        'institutes.Institute',
        blank=True,
        related_name='regional_managers',
        verbose_name=_('Managed Institutes'),
        help_text=_('For regional managers - institutes they supervise')
    )
    
    managed_institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='branch_managers',
        verbose_name=_('Managed Institute'),
        help_text=_('For branch managers - their institute')
    )
    
    institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_('Institute'),
        help_text=_('For employees - their institute')
    )
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.get_role_display()}"
    
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser
    
    def is_regional_manager(self):
        return self.role == self.Role.REGIONAL_MANAGER
    
    def is_branch_manager(self):
        return self.role == self.Role.BRANCH_MANAGER
    
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE
    
    def get_managed_institutes(self):
        """الحصول على المعاهد التي يديرها المستخدم"""
        if self.is_admin():
            from institutes.models import Institute
            return Institute.objects.all()
        elif self.is_regional_manager():
            return self.managed_institutes.all()
        elif self.is_branch_manager():
            if self.managed_institute:
                return self.managed_institute
            return None
        elif self.is_employee():
            if self.institute:
                return self.institute
            return None
        return None


class UserPermission(models.Model):
    """نموذج الصلاحيات المخصصة للمستخدمين"""
    
    class PermissionType(models.TextChoices):
        VIEW_ALL_INSTITUTES = 'view_all_institutes', _('View All Institutes')
        VIEW_OWN_INSTITUTE = 'view_own_institute', _('View Own Institute')
        MANAGE_USERS = 'manage_users', _('Manage Users')
        MANAGE_PROGRAMS = 'manage_programs', _('Manage Programs')
        REGISTER_CLIENTS = 'register_clients', _('Register Clients')
        ISSUE_PERMISSIONS = 'issue_permissions', _('Issue Permissions')
        VIEW_REPORTS = 'view_reports', _('View Reports')
        VIEW_OWN_REPORTS = 'view_own_reports', _('View Own Reports Only')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_permissions')
    permission = models.CharField(max_length=50, choices=PermissionType.choices)
    granted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('User Permission')
        verbose_name_plural = _('User Permissions')
        unique_together = ['user', 'permission']
        indexes = [
            models.Index(fields=['user', 'permission']),
            models.Index(fields=['granted']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.get_permission_display()}"
