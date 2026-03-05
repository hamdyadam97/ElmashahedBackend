from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client_list'),
    path('create/', views.ClientCreateView.as_view(), name='client_create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    # files
    path('export/pdf/', views.export_clients_pdf, name='export_clients_pdf'),
    path('export/excel/', views.export_clients_excel, name='export_clients_excel'),
    path('upload/', views.upload_clients, name='upload_clients'),
    # Search
    path('search/', views.ClientSearchView.as_view(), name='client_search'),
    
    # AJAX
    path('ajax/get-by-national-id/', views.GetClientByNationalIdView.as_view(), name='get_client_by_national_id'),
]
