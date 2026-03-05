from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserPermission


class UserPermissionInline(admin.TabularInline):
    model = UserPermission
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'get_full_name', 'email', 'role', 
        'get_institute', 'is_active', 'created_at'
    ]
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address')
        }),
        (_('Role & Institute'), {
            'fields': ('role', 'institute', 'managed_institute', 'managed_institutes')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    inlines = [UserPermissionInline]
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    get_full_name.short_description = _('Full Name')
    
    def get_institute(self, obj):
        if obj.is_admin():
            return _('All Institutes')
        elif obj.is_regional_manager():
            return f"{obj.managed_institutes.count()} institutes"
        elif obj.managed_institute:
            return obj.managed_institute.name
        elif obj.institute:
            return obj.institute.name
        return '-'
    get_institute.short_description = _('Institute')


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'granted', 'created_at']
    list_filter = ['permission', 'granted', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
