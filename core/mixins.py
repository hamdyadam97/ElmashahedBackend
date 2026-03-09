"""
Mixins مركزية للصلاحيات والفلترة حسب المعهد
Centralized Permission and Institute Scoping Mixins
"""
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin للتحقق من دور المستخدم
    """
    required_roles = []
    
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
            
        for role in self.required_roles:
            method_name = f'is_{role}'
            if hasattr(user, method_name) and getattr(user, method_name)():
                return True
        return False


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin للتحقق من أن المستخدم Admin"""
    required_roles = ['admin']


class RegionalManagerRequiredMixin(RoleRequiredMixin):
    """Mixin للتحقق من أن المستخدم مدير إقليمي أو أعلى"""
    required_roles = ['admin', 'regional_manager']


class BranchManagerRequiredMixin(RoleRequiredMixin):
    """Mixin للتحقق من أن المستخدم مدير فرع أو أعلى"""
    required_roles = ['admin', 'regional_manager', 'branch_manager']


class EmployeeRequiredMixin(RoleRequiredMixin):
    """Mixin للتحقق من أن المستخدم موظف أو أعلى"""
    required_roles = ['admin', 'regional_manager', 'branch_manager', 'employee']


class InstituteScopedMixin:
    """
    Mixin مركزي للفلترة حسب المعهد
    يقلل التكرار في جميع الـ Views
    ملاحظة: يجب استخدامه مع LoginRequiredMixin
    """
    institute_field = 'institute'  # اسم حقل المعهد في الموديل
    
    def get_user_institutes(self):
        """
        الحصول على المعاهد التي يمكن للمستخدم رؤيتها
        """
        user = self.request.user
        
        if user.is_admin() or user.is_superuser:
            return None  # None means all institutes
        elif user.is_regional_manager():
            return user.managed_institutes.all()
        elif user.is_branch_manager():
            if user.managed_institute:
                return [user.managed_institute]
            return []
        elif user.is_employee():
            if user.institute:
                return [user.institute]
            return []
        return []
    
    def get_queryset(self):
        """
        فلترة الـ Queryset تلقائياً حسب معهد المستخدم
        """
        queryset = super().get_queryset()
        user_institutes = self.get_user_institutes()
        
        if user_institutes is None:
            # Admin can see all
            return queryset
        elif not user_institutes:
            # User has no institute assigned
            return queryset.none()
        
        # Filter by institute field
        filter_kwargs = {f'{self.institute_field}__in': user_institutes}
        return queryset.filter(**filter_kwargs)


class InstituteScopedDiplomaMixin(InstituteScopedMixin):
    """Mixin للفلترة عبر حقل institute في Diploma"""
    institute_field = 'institute'


class InstituteScopedCourseMixin(InstituteScopedMixin):
    """Mixin للفلترة عبر حقل institute في Course"""
    institute_field = 'institute'


class InstituteScopedClientMixin(InstituteScopedMixin):
    """Mixin للفلترة عبر حقل institute في Client"""
    institute_field = 'institute'


class InstituteScopedPermissionMixin(InstituteScopedMixin):
    """Mixin للفلترة عبر حقل institute في PermissionSlip"""
    institute_field = 'institute'


class InstituteScopedRegistrationMixin(InstituteScopedMixin):
    """
    Mixin خاص للتسجيلات لأن لها علاقتين (diploma, course)
    """
    def get_queryset(self):
        queryset = super(InstituteScopedMixin, self).get_queryset()
        user = self.request.user
        
        if user.is_admin() or user.is_superuser:
            return queryset
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            return queryset.filter(
                Q(diploma__institute__in=institutes) |
                Q(course__institute__in=institutes)
            )
        elif user.is_branch_manager():
            institute = user.managed_institute
            if institute:
                return queryset.filter(
                    Q(diploma__institute=institute) |
                    Q(course__institute=institute)
                )
            return queryset.none()
        elif user.is_employee():
            institute = user.institute
            if institute:
                return queryset.filter(
                    Q(diploma__institute=institute) |
                    Q(course__institute=institute)
                )
            return queryset.none()
        return queryset.none()


class SearchMixin:
    """
    Mixin لإضافة وظيفة البحث بسهولة
    """
    search_fields = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        
        if search and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f'{field}__icontains': search})
            queryset = queryset.filter(q_objects)
        
        return queryset


class FilterMixin:
    """
    Mixin لإضافة وظيفة التصفية حسب معايير متعددة
    """
    filter_fields = {}
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        for param, field in self.filter_fields.items():
            value = self.request.GET.get(param)
            if value:
                queryset = queryset.filter(**{field: value})
        
        return queryset


class SoftDeleteMixin:
    """
    Mixin للحذف الناعم (Soft Delete)
    """
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        return self.post_delete_redirect()
    
    def post_delete_redirect(self):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.success(self.request, f'تم نقل "{self.object}" إلى الأرشيف بنجاح')
        return redirect(self.get_success_url())


# ============== Helper Functions ==============

def get_user_institute(user):
    """
    الحصول على المعهد الخاص بالمستخدم
    """
    if user.is_branch_manager():
        return user.managed_institute
    elif user.is_employee():
        return user.institute
    return None


def can_view_institute(user, institute):
    """
    التحقق مما إذا كان المستخدم يمكنه رؤية معهد معين
    """
    if user.is_admin():
        return True
    elif user.is_regional_manager():
        return institute in user.managed_institutes.all()
    elif user.is_branch_manager():
        return institute == user.managed_institute
    elif user.is_employee():
        return institute == user.institute
    return False
