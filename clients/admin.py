from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'national_id', 'phone', 'city', 'institute',
        'gender', 'status', 'registration_date'
    ]
    list_filter = ['status', 'gender', 'sector', 'institute', 'registration_date']
    search_fields = [
        'full_name', 'national_id', 'phone', 'email', 'city'
    ]
    date_hierarchy = 'registration_date'

    fieldsets = (
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'full_name', 'national_id')
        }),
        (_('Personal Details'), {
            'fields': ('gender', 'birth_date', 'sector')
        }),
        (_('Contact Info'), {
            'fields': ('phone', 'email', 'city', 'address')
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
