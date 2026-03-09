from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from core.models import BaseModel


class ProgramCategory(BaseModel):
    """فئة البرنامج (دبلومة أو دورة)"""
    
    class Type(models.TextChoices):
        DIPLOMA = 'diploma', _('Diploma')
        COURSE = 'course', _('Course')
    
    name = models.CharField(max_length=100, verbose_name=_('Category Name'))
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name=_('Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    class Meta:
        verbose_name = _('Program Category')
        verbose_name_plural = _('Program Categories')
        ordering = ['name']
        indexes = [
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Diploma(BaseModel):
    """نموذج الدبلومة"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        COMPLETED = 'completed', _('Completed')
    
    name = models.CharField(max_length=200, verbose_name=_('Diploma Name'))
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Diploma Code'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.CASCADE,
        related_name='diplomas',
        verbose_name=_('Institute')
    )
    
    category = models.ForeignKey(
        ProgramCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diplomas',
        verbose_name=_('Category')
    )
    
    # مدة الدراسة (سنتان للدبلومات)
    duration_months = models.PositiveIntegerField(
        default=24,
        validators=[MinValueValidator(1)],
        verbose_name=_('Duration (Months)')
    )
    
    # المواعيد
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))
    registration_start_date = models.DateField(verbose_name=_('Registration Start Date'))
    registration_end_date = models.DateField(verbose_name=_('Registration End Date'))
    
    # التكلفة
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Fees')
    )
    
    # الحالة
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_('Status')
    )
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Diploma')
        verbose_name_plural = _('Diplomas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['institute', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.institute.name}"
    
    def get_registered_clients_count(self):
        return self.registrations.count()


class Course(BaseModel):
    """نموذج الدورة"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        COMPLETED = 'completed', _('Completed')
    
    name = models.CharField(max_length=200, verbose_name=_('Course Name'))
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Course Code'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('Institute')
    )
    
    category = models.ForeignKey(
        ProgramCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name=_('Category')
    )
    
    # مدة الدراسة (6 أشهر للدورات)
    duration_months = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(1)],
        verbose_name=_('Duration (Months)')
    )
    
    # المواعيد
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))
    registration_start_date = models.DateField(verbose_name=_('Registration Start Date'))
    registration_end_date = models.DateField(verbose_name=_('Registration End Date'))
    
    # التكلفة
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Fees')
    )
    
    # الحالة
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_('Status')
    )
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['institute', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.institute.name}"
    
    def get_registered_clients_count(self):
        return self.registrations.count()


class ProgramRegistration(BaseModel):
    """نموذج تسجيل العميل في برنامج"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name=_('Client')
    )
    
    # يمكن أن يكون تسجيل في دبلومة أو دورة
    diploma = models.ForeignKey(
        Diploma,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='registrations',
        verbose_name=_('Diploma')
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='registrations',
        verbose_name=_('Course')
    )
    
    # الموظف الذي قام بالتسجيل
    registered_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='registrations_made',
        verbose_name=_('Registered By')
    )
    
    # تاريخ التسجيل والحالة
    registration_date = models.DateField(auto_now_add=True, verbose_name=_('Registration Date'))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
        verbose_name=_('Status')
    )
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Program Registration')
        verbose_name_plural = _('Program Registrations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['diploma']),
            models.Index(fields=['course']),
            models.Index(fields=['registered_by']),
            models.Index(fields=['registration_date']),
        ]
    
    def __str__(self):
        program = self.diploma or self.course
        return f"{self.client} - {program}"
    
    def get_program_type(self):
        if self.diploma:
            return 'diploma'
        return 'course'
    
    def get_program(self):
        return self.diploma or self.course
