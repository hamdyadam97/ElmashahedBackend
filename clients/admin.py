from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'national_id', 'phone', 'institute', 
        'gender', 'status', 'registration_date'
    ]
    list_filter = ['status', 'gender', 'institute', 'registration_date']
    search_fields = [
        'full_name', 'national_id', 'phone', 'email', 'address'
    ]
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'full_name', 'national_id')
        }),
        (_('Personal Details'), {
            'fields': ('gender', 'birth_date')
        }),
        (_('Contact Info'), {
            'fields': ('phone', 'email', 'address')
        }),
        (_('Institute & Registration'), {
            'fields': ('institute', 'registered_by', 'status')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('registration_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['full_name', 'registration_date', 'created_at', 'updated_at']
