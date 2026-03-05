from django.urls import path
from . import views

app_name = 'programs'

urlpatterns = [
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.ProgramCategoryDeleteView.as_view(), name='category_delete'),
    # Diplomas
    path('diplomas/', views.DiplomaListView.as_view(), name='diploma_list'),
    path('diplomas/create/', views.DiplomaCreateView.as_view(), name='diploma_create'),
    path('diplomas/<int:pk>/', views.DiplomaDetailView.as_view(), name='diploma_detail'),
    path('diplomas/<int:pk>/edit/', views.DiplomaUpdateView.as_view(), name='diploma_update'),
    path('diplomas/<int:pk>/delete/', views.DiplomaDeleteView.as_view(), name='diploma_delete'),
    path('diplomas/upload_diplomas/', views.upload_diplomas, name='upload_diplomas'),
    path('diplomas/export_excel/', views.export_diplomas_excel, name='export_excel_diplomas'),
    path('diplomas/export_pdf/', views.export_diplomas_pdf, name='export_pdf_diplomas'),

# ونفس الشيء للكورسات...
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('courses/export_courses_pdf/', views.export_courses_pdf, name='export_courses_pdf'),
    path('courses/upload/', views.upload_courses, name='upload_courses'),
    # Registrations
    path('registrations/', views.RegistrationListView.as_view(), name='registration_list'),
    path('registrations/create/', views.RegistrationCreateView.as_view(), name='registration_create'),
    path('registrations/<int:pk>/', views.RegistrationDetailView.as_view(), name='registration_detail'),
]
