from django import forms
from .models import Account, Asset, AssetValueHistory, Contribution


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['type', 'year', 'annual_contribution_limit']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
            'annual_contribution_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


from django import forms
from .models import Asset, Account


class AssetForm(forms.ModelForm):

    affects_contribution_room = forms.ChoiceField(
        choices=[
            (True, "Yes — counts toward contribution room"),
            (False, "No — does NOT count toward contribution room"),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Asset
        fields = [
            'account',
            'name',
            'ticker',
            'asset_type',
            'purchase_date',
            'purchase_price',
            'quantity',
            'affects_contribution_room'
        ]

        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'ticker': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_type': forms.Select(attrs={'class': 'form-select'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)

        # ensure correct initial value when editing
        if self.instance and self.instance.pk:
            self.fields['affects_contribution_room'].initial = (
                self.instance.affects_contribution_room
            )

    def clean_affects_contribution_room(self):
        value = self.cleaned_data.get("affects_contribution_room")

        if value in [True, "True", "true", "1", "on"]:
            return True
        if value in [False, "False", "false", "0", None]:
            return False

        return None


class AssetValueHistoryForm(forms.ModelForm):
    class Meta:
        model = AssetValueHistory
        fields = ['date', 'value']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        }


class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['account', 'year', 'amount']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)
