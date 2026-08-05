from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('api/diplomas/', views.api_diplomas, name='api_diplomas'),
    path('api/search-client/', views.api_search_client, name='api_search_client'),
    path('issue/', views.IssueView.as_view(), name='issue'),
    path('<str:ref_code>/', views.LandingView.as_view(), name='landing_ref'),
]
