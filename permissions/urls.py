from django.urls import path
from . import views

app_name = 'permissions'

urlpatterns = [
    path('', views.PermissionListView.as_view(), name='permission_list'),
    path('create/', views.PermissionCreateView.as_view(), name='permission_create'),
    path('<int:pk>/', views.PermissionDetailView.as_view(), name='permission_detail'),
    path('<int:pk>/pdf/', views.PermissionPDFView.as_view(), name='permission_pdf'),
    path('<int:pk>/download/', views.PermissionDownloadView.as_view(), name='permission_download'),
    path('<int:pk>/cancel/', views.PermissionCancelView.as_view(), name='permission_cancel'),
    
    # Templates
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.TemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.TemplateUpdateView.as_view(), name='template_update'),
]
