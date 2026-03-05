from django.urls import path
from . import views

app_name = 'institutes'

urlpatterns = [
    path('', views.InstituteListView.as_view(), name='institute_list'),
    path('create/', views.InstituteCreateView.as_view(), name='institute_create'),
    path('<int:pk>/', views.InstituteDetailView.as_view(), name='institute_detail'),
    path('<int:pk>/edit/', views.InstituteUpdateView.as_view(), name='institute_update'),
    path('<int:pk>/delete/', views.InstituteDeleteView.as_view(), name='institute_delete'),
    
    # PDF Template
    path('<int:pk>/template/', views.PDFTemplateView.as_view(), name='pdf_template'),
    path('<int:pk>/template/edit/', views.PDFTemplateEditView.as_view(), name='pdf_template_edit'),
    path('upload_data/', views.upload_data, name='upload_data'),
    path('export_excel/', views.export_excel, name='export_excel'),
    path('export_pdf/', views.export_institutes_pdf, name='export_pdf'),
]
