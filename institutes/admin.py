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
            'fields': ('pdf_template', 'signature_image', 'stamp_image', 'registration_officer', 'background_img'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['registration_officer']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'registration_officer':
            from accounts.models import User
            kwargs['queryset'] = User.objects.filter(
                is_active=True,
                role__in=[User.Role.EMPLOYEE, User.Role.BRANCH_MANAGER]
            ).order_by('first_name', 'last_name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
