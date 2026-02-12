from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    # Auth
    path('', CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Assets
    path('accountinfo/', views.show_assets, name='accountinfo'),
    path('sync-tags/', views.sync_tags, name='sync_tags'),

    # Reports
    path('reports/', views.show_reports, name='show_reports'),
    path('download-logs/', views.download_logs, name='download_logs'),
    path('export-reports/', views.export_reports, name='export_reports'),

    # API
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/analytics/', views.api_analytics, name='api_analytics'),

    # AI Analytics
    path('analytics/', views.analytics_view, name='analytics'),
]
