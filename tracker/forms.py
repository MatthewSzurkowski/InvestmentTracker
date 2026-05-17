from django import forms
from .models import Account, Asset, Trade, AssetPriceHistory


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['type', 'year', 'annual_contribution_limit']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
            'annual_contribution_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'ticker', 'asset_type', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vanguard XEQT'}),
            'ticker': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., XEQT'}),
            'asset_type': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }


class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = ['asset', 'account', 'trade_type', 'quantity', 'purchase_price', 'date', 'affects_contribution_room']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'trade_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'affects_contribution_room': forms.Select(choices=[
                (True, 'Yes'),
                (False, 'No'),
            ], attrs={'class': 'form-select'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['asset'].queryset = Asset.objects.filter(user=user)
            self.fields['account'].queryset = Account.objects.filter(user=user)


class AssetPriceHistoryForm(forms.ModelForm):
    class Meta:
        model = AssetPriceHistory
        fields = ['date', 'price']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        }
