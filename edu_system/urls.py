"""
URL configuration for edu_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """Health check endpoint for Docker and monitoring."""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
        }, status=503)

# Custom error handlers
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('institutes/', include('institutes.urls')),
    path('programs/', include('programs.urls')),
    path('clients/', include('clients.urls')),
    path('permissions/', include('permissions.urls')),
    path('core/', include('core.urls')),
    path('certificate/', include('portal.urls', namespace='portal')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Custom 404 page for testing in DEBUG mode
    from django.http import Http404
    urlpatterns += [
        path('test-404/', lambda r: (_ for _ in ()).throw(Http404())),
    ]

# Error handlers
handler404 = 'edu_system.urls.custom_404'
handler500 = 'edu_system.urls.custom_500'
