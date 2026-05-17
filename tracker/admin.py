from django.contrib import admin
from .models import Account, Asset, Trade, AssetPriceHistory


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'year', 'annual_contribution_limit']
    list_filter = ['type', 'year']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['user', 'ticker', 'name', 'asset_type', 'currency']
    list_filter = ['asset_type', 'currency']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'account', 'trade_type', 'quantity', 'purchase_price', 'date']
    list_filter = ['trade_type', 'date']


@admin.register(AssetPriceHistory)
class AssetPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['asset', 'date', 'price']
    list_filter = ['date']
