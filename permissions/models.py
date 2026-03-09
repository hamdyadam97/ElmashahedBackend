from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

from core.models import BaseModel


class PermissionSlip(BaseModel):
    """نموذج إذن/تصريح الدراسة"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        EXPIRED = 'expired', _('Expired')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # رقم الإذن الفريد
    permission_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Permission Number')
    )
    
    # العميل
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='permissions',
        verbose_name=_('Client')
    )
    
    # المعهد
    institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.CASCADE,
        related_name='permissions',
        verbose_name=_('Institute')
    )
    
    # البرنامج (دبلومة أو دورة)
    diploma = models.ForeignKey(
        'programs.Diploma',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permissions',
        verbose_name=_('Diploma')
    )
    
    course = models.ForeignKey(
        'programs.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permissions',
        verbose_name=_('Course')
    )
    
    # نوع البرنامج
    program_type = models.CharField(
        max_length=20,
        choices=[('diploma', _('Diploma')), ('course', _('Course'))],
        verbose_name=_('Program Type')
    )
    
    # الموظف الذي أصدر الإذن
    issued_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='permissions_issued',
        verbose_name=_('Issued By')
    )
    
    # تاريخ الإصدار والصلاحية
    issue_date = models.DateField(auto_now_add=True, verbose_name=_('Issue Date'))
    expiry_date = models.DateField(verbose_name=_('Expiry Date'))
    
    # الحالة
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_('Status')
    )
    
    # ملف PDF
    pdf_file = models.FileField(
        upload_to='permissions/pdfs/%Y/%m/',
        blank=True,
        verbose_name=_('PDF File')
    )
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Permission Slip')
        verbose_name_plural = _('Permission Slips')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['permission_number']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['institute', 'status']),
            models.Index(fields=['issued_by']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        program = self.diploma or self.course
        return f"{self.permission_number} - {self.client.full_name} - {program}"
    
    def save(self, *args, **kwargs):
        # توليد رقم الإذن تلقائياً إذا لم يكن موجوداً
        if not self.permission_number:
            self.permission_number = self.generate_permission_number()
        
        # تحديد نوع البرنامج
        if self.diploma:
            self.program_type = 'diploma'
            self.institute = self.diploma.institute
        elif self.course:
            self.program_type = 'course'
            self.institute = self.course.institute
        
        super().save(*args, **kwargs)
    
    def generate_permission_number(self):
        """توليد رقم إذن فريد"""
        year = timezone.now().year
        unique_id = str(uuid.uuid4().int)[:6]
        return f"PERM-{year}-{unique_id}"
    
    def get_program(self):
        """الحصول على البرنامج (دبلومة أو دورة)"""
        return self.diploma or self.course
    
    def is_valid(self):
        """التحقق من صلاحية الإذن"""
        if self.status != self.Status.ACTIVE:
            return False
        return timezone.now().date() <= self.expiry_date
    
    def get_program_name(self):
        """الحصول على اسم البرنامج"""
        program = self.get_program()
        return program.name if program else '-'
    
    def get_program_duration(self):
        """الحصول على مدة البرنامج"""
        program = self.get_program()
        return program.duration_months if program else 0
    
    def get_program_dates(self):
        """الحصول على تواريخ البرنامج"""
        program = self.get_program()
        if program:
            return {
                'start': program.start_date,
                'end': program.end_date
            }
        return None


class PermissionTemplate(BaseModel):
    """قوالب PDF للأذونات لكل معهد"""
    
    institute = models.OneToOneField(
        'institutes.Institute',
        on_delete=models.CASCADE,
        related_name='permission_template',
        verbose_name=_('Institute')
    )
    
    # محتوى القالب
    header_content = models.TextField(
        verbose_name=_('Header Content'),
        help_text=_('HTML content for PDF header')
    )
    
    body_content = models.TextField(
        verbose_name=_('Body Content'),
        help_text=_('HTML content for PDF body')
    )
    
    footer_content = models.TextField(
        verbose_name=_('Footer Content'),
        help_text=_('HTML content for PDF footer')
    )
    
    # CSS مخصص
    custom_css = models.TextField(
        blank=True,
        verbose_name=_('Custom CSS'),
        help_text=_('Custom CSS styles for PDF')
    )
    
    # الإعدادات
    page_size = models.CharField(
        max_length=20,
        default='A4',
        verbose_name=_('Page Size')
    )
    
    orientation = models.CharField(
        max_length=20,
        default='portrait',
        choices=[('portrait', _('Portrait')), ('landscape', _('Landscape'))],
        verbose_name=_('Orientation')
    )
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Permission Template')
        verbose_name_plural = _('Permission Templates')
        indexes = [
            models.Index(fields=['institute']),
        ]
    
    def __str__(self):
        return f"Template for {self.institute.name}"
