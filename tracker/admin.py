from django.contrib import admin
from .models import Account, Asset, Contribution, AssetValueHistory


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'year', 'annual_contribution_limit']
    list_filter = ['type', 'year']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'ticker', 'asset_type', 'account', 'purchase_date', 'purchase_price', 'quantity']
    list_filter = ['asset_type']


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ['user', 'account', 'year', 'amount', 'auto_generated', 'created_at']
    list_filter = ['auto_generated', 'year']


@admin.register(AssetValueHistory)
class AssetValueHistoryAdmin(admin.ModelAdmin):
    list_display = ['asset', 'date', 'value']
    list_filter = ['date']
