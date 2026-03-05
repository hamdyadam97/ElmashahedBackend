from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Client(BaseModel):
    """نموذج العميل/الطالب"""
    
    class Gender(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        GRADUATED = 'graduated', _('Graduated')
    
    # البيانات الشخصية
    first_name = models.CharField(max_length=100, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=100, verbose_name=_('Last Name'))
    full_name = models.CharField(max_length=200, verbose_name=_('Full Name'))
    
    # رقم الهوية/البطاقة
    national_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('National ID')
    )
    
    # الجنس والتاريخ
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        verbose_name=_('Gender')
    )
    birth_date = models.DateField(verbose_name=_('Birth Date'))
    
    # معلومات الاتصال
    phone = models.CharField(max_length=20, verbose_name=_('Phone'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    address = models.TextField(verbose_name=_('Address'))
    
    # المعهد
    institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name=_('Institute')
    )
    
    # الموظف الذي قام بتسجيل العميل
    registered_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients_registered',
        verbose_name=_('Registered By')
    )
    
    # الحالة
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_('Status')
    )
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    # التواريخ
    registration_date = models.DateField(auto_now_add=True, verbose_name=_('Registration Date'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.national_id}"
    
    def save(self, *args, **kwargs):
        # توليد الاسم الكامل تلقائياً
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)
    
    def get_active_registrations(self):
        """الحصول على التسجيلات النشطة"""
        return self.registrations.filter(status__in=['pending', 'confirmed'])
    
    def get_total_permissions_count(self):
        """عدد الأذونات المستخرجة"""
        return self.permissions.count()
    
    def get_diplomas(self):
        """الحصول على الدبلومات المسجل فيها"""
        return self.registrations.filter(diploma__isnull=False)
    
    def get_courses(self):
        """الحصول على الدورات المسجل فيها"""
        return self.registrations.filter(course__isnull=False)
