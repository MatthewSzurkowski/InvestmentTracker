import json
from decimal import Decimal
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages

from .models import Account, Asset, Contribution, AssetValueHistory
from .forms import AccountForm, AssetForm, AssetValueHistoryForm, ContributionForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user
    assets = list(Asset.objects.filter(user=user).select_related('account').prefetch_related('value_history'))
    accounts = Account.objects.filter(user=user)

    portfolio_history = _build_portfolio_history(assets)

    current_year = date.today().year
    contribution_data = []
    for account in accounts.filter(year=current_year):
        contribution_data.append({
            'label': account.type,
            'limit': float(account.annual_contribution_limit),
            'used': float(account.total_contributions()),
            'remaining': float(account.remaining_room()),
            'status': account.room_status(),
        })

    total_value = sum(a.current_value() for a in assets)
    total_cost = sum(a.purchase_value() for a in assets)
    total_gain = total_value - total_cost

    context = {
        'portfolio_history_json': json.dumps(portfolio_history),
        'contribution_data_json': json.dumps(contribution_data),
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain': total_gain,
        'asset_count': len(assets),
        'account_count': accounts.count(),
    }
    return render(request, 'tracker/dashboard.html', context)


def _build_portfolio_history(assets):
    if not assets:
        return {'labels': [], 'values': []}

    all_dates = set()
    for asset in assets:
        for vh in asset.value_history.all():
            all_dates.add(vh.date)
        all_dates.add(asset.purchase_date)

    if not all_dates:
        return {'labels': [], 'values': []}

    sorted_dates = sorted(all_dates)
    labels = []
    values = []

    for d in sorted_dates:
        total = Decimal('0')
        for asset in assets:
            if asset.purchase_date > d:
                continue
            latest_vh = None
            for vh in sorted(asset.value_history.all(), key=lambda x: x.date, reverse=True):
                if vh.date <= d:
                    latest_vh = vh
                    break
            if latest_vh:
                total += latest_vh.value * asset.quantity
            else:
                total += asset.purchase_value()
        labels.append(d.strftime('%Y-%m-%d'))
        values.append(float(total))

    return {'labels': labels, 'values': values}


@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user)
    account_data = []
    for account in accounts:
        account_data.append({
            'account': account,
            'total_contributions': account.total_contributions(),
            'remaining_room': account.remaining_room(),
            'status': account.room_status(),
        })
    return render(request, 'tracker/accounts.html', {'account_data': account_data})


@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            messages.success(request, 'Account created.')
            return redirect('account_list')
    else:
        form = AccountForm()
    return render(request, 'tracker/account_form.html', {'form': form, 'title': 'Add Account'})


@login_required
def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account updated.')
            return redirect('account_list')
    else:
        form = AccountForm(instance=account)
    return render(request, 'tracker/account_form.html', {'form': form, 'title': 'Edit Account'})


@login_required
def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
        messages.success(request, 'Account deleted.')
        return redirect('account_list')
    return render(request, 'tracker/confirm_delete.html', {'object': account, 'object_type': 'Account'})


@login_required
def asset_list(request):
    assets = Asset.objects.filter(user=request.user).select_related('account')
    asset_data = []
    for asset in assets:
        asset_data.append({
            'asset': asset,
            'current_value': asset.current_value(),
            'gain_loss': asset.gain_loss(),
            'gain_loss_pct': asset.gain_loss_pct(),
        })
    return render(request, 'tracker/investments.html', {'asset_data': asset_data})


@login_required
def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(user=request.user, data=request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.user = request.user
            asset.save()
            messages.success(request, 'Investment added. Contribution automatically recorded.')
            return redirect('asset_list')
    else:
        form = AssetForm(user=request.user)
    return render(request, 'tracker/asset_form.html', {'form': form, 'title': 'Add Investment'})


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AssetForm(user=request.user, data=request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Investment updated.')
            return redirect('asset_list')
    else:
        form = AssetForm(user=request.user, instance=asset)
    return render(request, 'tracker/asset_form.html', {'form': form, 'title': 'Edit Investment'})


@login_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Investment deleted.')
        return redirect('asset_list')
    return render(request, 'tracker/confirm_delete.html', {'object': asset, 'object_type': 'Investment'})


# @login_required
# def asset_update_value(request, pk):
#     asset = get_object_or_404(Asset, pk=pk, user=request.user)
#     if request.method == 'POST':
#         form = AssetValueHistoryForm(request.POST)
#         if form.is_valid():
#             vh = form.save(commit=False)
#             vh.asset = asset
#             vh.save()
#             messages.success(request, 'Value updated.')
#             return redirect('asset_list')
#     else:
#         form = AssetValueHistoryForm(initial={'date': date.today()})
#     return render(request, 'tracker/value_form.html', {'form': form, 'asset': asset})


@login_required
def contribution_list(request):
    contributions = Contribution.objects.filter(user=request.user).select_related('account')
    return render(request, 'tracker/contributions.html', {'contributions': contributions})


@login_required
def contribution_create(request):
    if request.method == 'POST':
        form = ContributionForm(user=request.user, data=request.POST)
        if form.is_valid():
            contrib = form.save(commit=False)
            contrib.user = request.user
            contrib.auto_generated = False
            contrib.save()
            messages.success(request, 'Contribution recorded.')
            return redirect('account_list')
    else:
        form = ContributionForm(user=request.user)
    return render(request, 'tracker/contribution_form.html', {'form': form, 'title': 'Add Contribution'})
