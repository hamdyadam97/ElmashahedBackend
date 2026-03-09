"""
Core Views - Archive (البوقايل) and Utilities
"""
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

from accounts.models import User
from institutes.models import Institute
from clients.models import Client
from programs.models import Diploma, Course, ProgramCategory, ProgramRegistration
from permissions.models import PermissionSlip
from core.mixins import AdminRequiredMixin, BranchManagerRequiredMixin

logger = logging.getLogger('edu_system')


class ArchiveView(LoginRequiredMixin, TemplateView):
    """
    صفحة الأرشيف (البوقايل) - تعرض كل العناصر المحذوفة
    """
    template_name = 'core/archive.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # فلترة حسب نوع المحتوى المطلوب
        content_type = self.request.GET.get('type', 'all')
        search_query = self.request.GET.get('q', '')
        
        # العملاء المحذوفين
        context['deleted_clients'] = self._get_deleted_clients(user, search_query if content_type in ['all', 'clients'] else '')
        
        # الدبلومات المحذوفة
        context['deleted_diplomas'] = self._get_deleted_diplomas(user, search_query if content_type in ['all', 'diplomas'] else '')
        
        # الدورات المحذوفة
        context['deleted_courses'] = self._get_deleted_courses(user, search_query if content_type in ['all', 'courses'] else '')
        
        # المعاهد المحذوفة (Admin فقط)
        if user.is_admin():
            context['deleted_institutes'] = self._get_deleted_institutes(search_query if content_type in ['all', 'institutes'] else '')
        
        # الأذونات المحذوفة
        context['deleted_permissions'] = self._get_deleted_permissions(user, search_query if content_type in ['all', 'permissions'] else '')
        
        # الفئات المحذوفة (Admin فقط)
        if user.is_admin():
            context['deleted_categories'] = self._get_deleted_categories(search_query if content_type in ['all', 'categories'] else '')
        
        # إحصائيات
        context['total_deleted'] = (
            context['deleted_clients'].count() +
            context['deleted_diplomas'].count() +
            context['deleted_courses'].count() +
            (context.get('deleted_institutes', []).count() if user.is_admin() else 0) +
            context['deleted_permissions'].count() +
            (context.get('deleted_categories', []).count() if user.is_admin() else 0)
        )
        
        context['content_type'] = content_type
        context['search_query'] = search_query
        
        return context
    
    def _get_deleted_clients(self, user, search_query=''):
        """الحصول على العملاء المحذوفين حسب صلاحيات المستخدم"""
        queryset = Client.all_objects.filter(is_deleted=True)
        
        if user.is_admin():
            pass  # See all
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = queryset.filter(institute__in=institutes)
        elif user.is_branch_manager() and user.managed_institute:
            queryset = queryset.filter(institute=user.managed_institute)
        elif user.is_employee() and user.institute:
            queryset = queryset.filter(institute=user.institute)
        else:
            queryset = queryset.none()
        
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(national_id__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        return queryset.select_related('institute', 'registered_by').order_by('-updated_at')[:50]
    
    def _get_deleted_diplomas(self, user, search_query=''):
        """الحصول على الدبلومات المحذوفة"""
        queryset = Diploma.all_objects.filter(is_deleted=True)
        
        if user.is_admin():
            pass
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = queryset.filter(institute__in=institutes)
        elif user.is_branch_manager() and user.managed_institute:
            queryset = queryset.filter(institute=user.managed_institute)
        elif user.is_employee() and user.institute:
            queryset = queryset.filter(institute=user.institute)
        else:
            queryset = queryset.none()
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query)
            )
        
        return queryset.select_related('institute').order_by('-updated_at')[:50]
    
    def _get_deleted_courses(self, user, search_query=''):
        """الحصول على الدورات المحذوفة"""
        queryset = Course.all_objects.filter(is_deleted=True)
        
        if user.is_admin():
            pass
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = queryset.filter(institute__in=institutes)
        elif user.is_branch_manager() and user.managed_institute:
            queryset = queryset.filter(institute=user.managed_institute)
        elif user.is_employee() and user.institute:
            queryset = queryset.filter(institute=user.institute)
        else:
            queryset = queryset.none()
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query)
            )
        
        return queryset.select_related('institute').order_by('-updated_at')[:50]
    
    def _get_deleted_institutes(self, search_query=''):
        """الحصول على المعاهد المحذوفة (Admin فقط)"""
        queryset = Institute.all_objects.filter(is_deleted=True)
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        return queryset.order_by('-updated_at')[:50]
    
    def _get_deleted_permissions(self, user, search_query=''):
        """الحصول على الأذونات المحذوفة"""
        queryset = PermissionSlip.all_objects.filter(is_deleted=True)
        
        if user.is_admin():
            pass
        elif user.is_regional_manager():
            institutes = user.managed_institutes.all()
            queryset = queryset.filter(institute__in=institutes)
        elif user.is_branch_manager() and user.managed_institute:
            queryset = queryset.filter(institute=user.managed_institute)
        elif user.is_employee() and user.institute:
            queryset = queryset.filter(institute=user.institute, issued_by=user)
        else:
            queryset = queryset.none()
        
        if search_query:
            queryset = queryset.filter(
                Q(permission_number__icontains=search_query) |
                Q(client__full_name__icontains=search_query)
            )
        
        return queryset.select_related('client', 'institute').order_by('-updated_at')[:50]
    
    def _get_deleted_categories(self, search_query=''):
        """الحصول على الفئات المحذوفة"""
        queryset = ProgramCategory.all_objects.filter(is_deleted=True)
        
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        return queryset.order_by('-updated_at')[:50]


class RestoreItemView(LoginRequiredMixin, View):
    """
    استعادة عنصر محذوف
    """
    def post(self, request):
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        
        if not item_type or not item_id:
            messages.error(request, 'بيانات غير صحيحة')
            return redirect('core:archive')
        
        try:
            item = self._get_item(item_type, item_id, request.user)
            if item:
                item.restore()
                logger.info(f'{item_type} {item_id} restored by {request.user.username}')
                messages.success(request, f'تم استعادة "{item}" بنجاح')
            else:
                messages.error(request, 'ليس لديك صلاحية لاستعادة هذا العنصر')
        except Exception as e:
            logger.error(f'Error restoring {item_type} {item_id}: {str(e)}')
            messages.error(request, 'حدث خطأ أثناء الاستعادة')
        
        return redirect('core:archive')
    
    def _get_item(self, item_type, item_id, user):
        """الحصول على العنصر والتحقق من الصلاحيات"""
        
        if item_type == 'client':
            item = get_object_or_404(Client.all_objects, id=item_id, is_deleted=True)
            if user.is_admin() or (user.is_regional_manager() and item.institute in user.managed_institutes.all()) or \
               (user.is_branch_manager() and item.institute == user.managed_institute) or \
               (user.is_employee() and item.institute == user.institute):
                return item
                
        elif item_type == 'diploma':
            item = get_object_or_404(Diploma.all_objects, id=item_id, is_deleted=True)
            if user.is_admin() or (user.is_regional_manager() and item.institute in user.managed_institutes.all()) or \
               (user.is_branch_manager() and item.institute == user.managed_institute) or \
               (user.is_employee() and item.institute == user.institute):
                return item
                
        elif item_type == 'course':
            item = get_object_or_404(Course.all_objects, id=item_id, is_deleted=True)
            if user.is_admin() or (user.is_regional_manager() and item.institute in user.managed_institutes.all()) or \
               (user.is_branch_manager() and item.institute == user.managed_institute) or \
               (user.is_employee() and item.institute == user.institute):
                return item
                
        elif item_type == 'institute':
            if not user.is_admin():
                return None
            return get_object_or_404(Institute.all_objects, id=item_id, is_deleted=True)
            
        elif item_type == 'permission':
            item = get_object_or_404(PermissionSlip.all_objects, id=item_id, is_deleted=True)
            if user.is_admin() or (user.is_regional_manager() and item.institute in user.managed_institutes.all()) or \
               (user.is_branch_manager() and item.institute == user.managed_institute) or \
               (user.is_employee() and item.issued_by == user):
                return item
                
        elif item_type == 'category':
            if not user.is_admin():
                return None
            return get_object_or_404(ProgramCategory.all_objects, id=item_id, is_deleted=True)
        
        return None


class PermanentDeleteView(AdminRequiredMixin, View):
    """
    حذف نهائي للعنصر (يحتاج Admin)
    """
    def post(self, request):
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        
        if not item_type or not item_id:
            messages.error(request, 'بيانات غير صحيحة')
            return redirect('core:archive')
        
        try:
            item = self._get_item_for_permanent_delete(item_type, item_id)
            item_name = str(item)
            item.delete()  # Delete permanently
            logger.warning(f'{item_type} {item_id} ({item_name}) permanently deleted by {request.user.username}')
            messages.success(request, f'تم الحذف النهائي لـ "{item_name}"')
        except Exception as e:
            logger.error(f'Error permanently deleting {item_type} {item_id}: {str(e)}')
            messages.error(request, 'حدث خطأ أثناء الحذف')
        
        return redirect('core:archive')
    
    def _get_item_for_permanent_delete(self, item_type, item_id):
        """الحصول على العنصر للحذف النهائي"""
        if item_type == 'client':
            return get_object_or_404(Client.all_objects, id=item_id, is_deleted=True)
        elif item_type == 'diploma':
            return get_object_or_404(Diploma.all_objects, id=item_id, is_deleted=True)
        elif item_type == 'course':
            return get_object_or_404(Course.all_objects, id=item_id, is_deleted=True)
        elif item_type == 'institute':
            return get_object_or_404(Institute.all_objects, id=item_id, is_deleted=True)
        elif item_type == 'permission':
            return get_object_or_404(PermissionSlip.all_objects, id=item_id, is_deleted=True)
        elif item_type == 'category':
            return get_object_or_404(ProgramCategory.all_objects, id=item_id, is_deleted=True)
        raise ValueError(f'Unknown item type: {item_type}')


class EmptyTrashView(AdminRequiredMixin, View):
    """
    تفريغ الأرشيف بالكامل (يحذف كل العناصر المحذوفة نهائياً)
    """
    def post(self, request):
        try:
            # عدد العناصر قبل الحذف
            counts = {
                'clients': Client.all_objects.filter(is_deleted=True).count(),
                'diplomas': Diploma.all_objects.filter(is_deleted=True).count(),
                'courses': Course.all_objects.filter(is_deleted=True).count(),
                'institutes': Institute.all_objects.filter(is_deleted=True).count(),
                'permissions': PermissionSlip.all_objects.filter(is_deleted=True).count(),
                'categories': ProgramCategory.all_objects.filter(is_deleted=True).count(),
            }
            
            total = sum(counts.values())
            
            # الحذف النهائي
            Client.all_objects.filter(is_deleted=True).delete()
            Diploma.all_objects.filter(is_deleted=True).delete()
            Course.all_objects.filter(is_deleted=True).delete()
            Institute.all_objects.filter(is_deleted=True).delete()
            PermissionSlip.all_objects.filter(is_deleted=True).delete()
            ProgramCategory.all_objects.filter(is_deleted=True).delete()
            
            logger.warning(f'Trash emptied by {request.user.username}. Deleted: {counts}')
            messages.success(request, f'تم تفريغ الأرشيف بنجاح. تم حذف {total} عنصر نهائياً.')
            
        except Exception as e:
            logger.error(f'Error emptying trash: {str(e)}')
            messages.error(request, 'حدث خطأ أثناء تفريغ الأرشيف')
        
        return redirect('core:archive')


class ArchiveStatsView(LoginRequiredMixin, View):
    """
    إحصائيات الأرشيف (AJAX)
    """
    def get(self, request):
        user = request.user
        
        stats = {
            'clients': self._count_deleted_clients(user),
            'diplomas': self._count_deleted_diplomas(user),
            'courses': self._count_deleted_courses(user),
            'permissions': self._count_deleted_permissions(user),
        }
        
        if user.is_admin():
            stats['institutes'] = Institute.all_objects.filter(is_deleted=True).count()
            stats['categories'] = ProgramCategory.all_objects.filter(is_deleted=True).count()
        
        stats['total'] = sum(stats.values())
        
        return JsonResponse(stats)
    
    def _count_deleted_clients(self, user):
        queryset = Client.all_objects.filter(is_deleted=True)
        return self._filter_by_user_permissions(queryset, user, 'institute')
    
    def _count_deleted_diplomas(self, user):
        queryset = Diploma.all_objects.filter(is_deleted=True)
        return self._filter_by_user_permissions(queryset, user, 'institute')
    
    def _count_deleted_courses(self, user):
        queryset = Course.all_objects.filter(is_deleted=True)
        return self._filter_by_user_permissions(queryset, user, 'institute')
    
    def _count_deleted_permissions(self, user):
        queryset = PermissionSlip.all_objects.filter(is_deleted=True)
        return self._filter_by_user_permissions(queryset, user, 'institute')
    
    def _filter_by_user_permissions(self, queryset, user, institute_field):
        if user.is_admin():
            return queryset.count()
        elif user.is_regional_manager():
            return queryset.filter(**{f'{institute_field}__in': user.managed_institutes.all()}).count()
        elif user.is_branch_manager() and user.managed_institute:
            return queryset.filter(**{institute_field: user.managed_institute}).count()
        elif user.is_employee() and user.institute:
            return queryset.filter(**{institute_field: user.institute}).count()
        return 0
