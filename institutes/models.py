from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Institute(BaseModel):
    """نموذج المعهد/الفرع"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
    
    name = models.CharField(max_length=200, verbose_name=_('Institute Name'))
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Institute Code'))
    license_number = models.CharField(max_length=50, unique=True, verbose_name=_('License Number'))
    
    # العنوان
    address = models.TextField(verbose_name=_('Address'))
    city = models.CharField(max_length=100, verbose_name=_('City'))
    region = models.CharField(max_length=100, verbose_name=_('Region'))
    phone = models.CharField(max_length=20, verbose_name=_('Phone'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    
    # الشعار والتصميم
    logo = models.ImageField(upload_to='institutes/logos/', blank=True, verbose_name=_('Logo'))
    header_image = models.ImageField(upload_to='institutes/headers/', blank=True, verbose_name=_('Header Image'))
    footer_text = models.TextField(blank=True, verbose_name=_('Footer Text'))
    
    # إعدادات PDF
    pdf_template = models.TextField(
        blank=True,
        verbose_name=_('PDF Template'),
        help_text=_('Custom HTML template for permission PDF')
    )
    signature_image = models.ImageField(upload_to='institutes/signatures/', blank=True, verbose_name=_('Signature Image'))
    stamp_image = models.ImageField(upload_to='institutes/stamps/', blank=True, verbose_name=_('Stamp Image'))
    
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
        verbose_name = _('Institute')
        verbose_name_plural = _('Institutes')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['city', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_active_programs_count(self):
        return self.programs.filter(status='active').count()
    
    def get_active_diplomas_count(self):
        return self.diplomas.filter(status='active').count()
    
    def get_total_clients_count(self):
        return self.clients.count()
    
    def get_total_permissions_count(self):
        return self.permissions.count()
