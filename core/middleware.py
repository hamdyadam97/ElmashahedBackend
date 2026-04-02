"""
Core Middleware - Authentication & Security
"""
import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout

logger = logging.getLogger('edu_system')


class AuthenticationMiddleware:
    """
    Middleware للتحقق من تسجيل الدخول
    يضمن أن المستخدمين غير المسجلين لا يمكنهم الوصول للصفحات المحمية
    """
    
    # المسارات المسموح الوصول إليها بدون تسجيل دخول
    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/password_reset/',
        '/accounts/password_reset/done/',
        '/accounts/reset/',
        '/accounts/reset/done/',
        '/admin/login/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # التحقق من أن المسار ليس في قائمة الاستثناءات
        path = request.path_info
        
        # السماح بالوصول للـ static و media
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)
        
        # السماح بالوصول لصفحات المصادقة
        if any(path.startswith(exempt) for exempt in self.EXEMPT_URLS):
            return self.get_response(request)
        
        # التحقق من تسجيل الدخول
        if not request.user.is_authenticated:
            logger.warning(f'Unauthenticated access attempt to {path} from {request.META.get("REMOTE_ADDR")}')
            return redirect('accounts:login')
        
        # التحقق من أن المستخدم نشط
        if not request.user.is_active:
            logger.warning(f'Inactive user {request.user.username} attempted to access {path}')
            logout(request)
            return redirect('accounts:login')
        
        response = self.get_response(request)
        
        # إضافة headers لمنع caching للصفحات المحمية
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class SecurityHeadersMiddleware:
    """
    Middleware لإضافة headers أمنية
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # إضافة headers أمنية
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
