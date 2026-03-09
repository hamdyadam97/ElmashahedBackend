"""
URLs for Core App - Archive (البوقايل)
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Archive (البوقايل)
    path('archive/', views.ArchiveView.as_view(), name='archive'),
    path('archive/restore/', views.RestoreItemView.as_view(), name='restore_item'),
    path('archive/permanent-delete/', views.PermanentDeleteView.as_view(), name='permanent_delete'),
    path('archive/empty-trash/', views.EmptyTrashView.as_view(), name='empty_trash'),
    path('archive/stats/', views.ArchiveStatsView.as_view(), name='archive_stats'),
]
