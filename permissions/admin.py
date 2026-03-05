from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import PermissionSlip, PermissionTemplate


@admin.register(PermissionSlip)
class PermissionSlipAdmin(admin.ModelAdmin):
    list_display = [
        'permission_number', 'client', 'get_program', 
        'program_type', 'issued_by', 'issue_date', 'status'
    ]
    list_filter = ['status', 'program_type', 'issue_date', 'institute']
    search_fields = [
        'permission_number', 'client__full_name', 
        'client__national_id', 'diploma__name', 'course__name'
    ]
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        (_('Permission Info'), {
            'fields': ('permission_number', 'status')
        }),
        (_('Client'), {
            'fields': ('client',)
        }),
        (_('Program'), {
            'fields': ('diploma', 'course', 'program_type')
        }),
        (_('Institute & Issuer'), {
            'fields': ('institute', 'issued_by')
        }),
        (_('Dates'), {
            'fields': ('issue_date', 'expiry_date')
        }),
        (_('Files'), {
            'fields': ('pdf_file',),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['permission_number', 'issue_date', 'program_type']
    
    def get_program(self, obj):
        return obj.get_program()
    get_program.short_description = _('Program')


@admin.register(PermissionTemplate)
class PermissionTemplateAdmin(admin.ModelAdmin):
    list_display = ['institute', 'page_size', 'orientation', 'created_at']
    list_filter = ['page_size', 'orientation']
    search_fields = ['institute__name']
    
    fieldsets = (
        (_('Institute'), {
            'fields': ('institute',)
        }),
        (_('Content'), {
            'fields': ('header_content', 'body_content', 'footer_content')
        }),
        (_('Styling'), {
            'fields': ('custom_css', 'page_size', 'orientation'),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {
                'all': ('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css',)
        }
        js = (
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js',
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/xml/xml.min.js',  # للـ HTML
                'js/admin_preview.js',
            )


    # تحسين شكل التكست أريا في الأدمن لتكون أوسع للكود
    def formfield_for_dbfield(self, db_field, **kwargs):
        form_field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in ['header_content', 'body_content', 'footer_content', 'custom_css']:
            form_field.widget.attrs['rows'] = 10
            form_field.widget.attrs['style'] = 'font-family: monospace; width: 90%;'
        return form_field