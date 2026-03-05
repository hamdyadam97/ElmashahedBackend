from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ProgramCategory, Diploma, Course, ProgramRegistration


@admin.register(ProgramCategory)
class ProgramCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'description']
    list_filter = ['type']
    search_fields = ['name']


class ProgramRegistrationInline(admin.TabularInline):
    model = ProgramRegistration
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Diploma)
class DiplomaAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'institute', 'duration_months', 
        'start_date', 'end_date', 'status'
    ]
    list_filter = ['status', 'institute', 'start_date']
    search_fields = ['name', 'code', 'description']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('name', 'code', 'description', 'category')
        }),
        (_('Institute'), {
            'fields': ('institute',)
        }),
        (_('Duration & Dates'), {
            'fields': (
                'duration_months', 
                'start_date', 'end_date',
                'registration_start_date', 'registration_end_date'
            )
        }),
        (_('Fees'), {
            'fields': ('fees',)
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
    )
    
    inlines = [ProgramRegistrationInline]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'institute', 'duration_months', 
        'start_date', 'end_date', 'status'
    ]
    list_filter = ['status', 'institute', 'start_date']
    search_fields = ['name', 'code', 'description']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('name', 'code', 'description', 'category')
        }),
        (_('Institute'), {
            'fields': ('institute',)
        }),
        (_('Duration & Dates'), {
            'fields': (
                'duration_months', 
                'start_date', 'end_date',
                'registration_start_date', 'registration_end_date'
            )
        }),
        (_('Fees'), {
            'fields': ('fees',)
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
    )
    
    inlines = [ProgramRegistrationInline]


@admin.register(ProgramRegistration)
class ProgramRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'get_program', 'program_type', 
        'registered_by', 'registration_date', 'status'
    ]
    list_filter = ['status', 'registration_date']
    search_fields = [
        'client__full_name', 'client__national_id',
        'diploma__name', 'course__name'
    ]
    date_hierarchy = 'registration_date'
    
    def get_program(self, obj):
        return obj.get_program()
    get_program.short_description = _('Program')
    
    def program_type(self, obj):
        return obj.get_program_type()
    program_type.short_description = _('Type')
