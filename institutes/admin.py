from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Institute


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'license_number', 'city', 'region', 
        'status', 'created_at'
    ]
    list_filter = ['status', 'city', 'region', 'created_at']
    search_fields = ['name', 'code', 'license_number', 'address']
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('name', 'code', 'license_number', 'status')
        }),
        (_('Contact Info'), {
            'fields': ('address', 'city', 'region', 'phone', 'email')
        }),
        (_('Branding'), {
            'fields': ('logo', 'header_image', 'footer_text')
        }),
        (_('PDF Settings'), {
            'fields': ('pdf_template', 'signature_image', 'stamp_image'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
