from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Accounts
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/new/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),

    # Assets
    path('investments/', views.asset_list, name='asset_list'),
    path('investments/new/', views.asset_create, name='asset_create'),
    path('investments/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('investments/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    # path('investments/<int:pk>/update-value/', views.asset_update_value, name='asset_update_value'),

    # Contributions
    path('contributions/', views.contribution_list, name='contribution_list'),
    path('contributions/new/', views.contribution_create, name='contribution_create'),
]
