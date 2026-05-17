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

    # Securities (Assets)
    path('securities/', views.asset_list, name='asset_list'),
    path('securities/new/', views.asset_create, name='asset_create'),
    path('securities/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('securities/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    path('securities/<int:pk>/update-price/', views.asset_price_update, name='asset_price_update'),

    # Trades
    path('trades/', views.trade_list, name='trade_list'),
    path('trades/new/', views.trade_create, name='trade_create'),
    path('trades/<int:pk>/edit/', views.trade_edit, name='trade_edit'),
    path('trades/<int:pk>/delete/', views.trade_delete, name='trade_delete'),
]
