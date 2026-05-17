import json
from decimal import Decimal
from datetime import date
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.db.models import Sum, F, DecimalField

from .models import Account, Asset, Trade, AssetPriceHistory
from .forms import AccountForm, AssetForm, TradeForm, AssetPriceHistoryForm


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



def build_account_value_history(user):
    trades = (
        Trade.objects
        .filter(user=user)
        .select_related("account")
        .order_by("date")
    )

    # account -> month -> net value
    monthly = defaultdict(lambda: defaultdict(Decimal))

    for t in trades:
        account_name = f"{t.account.type} ({t.account.year})"
        month_key = t.date.strftime("%Y-%m")

        delta = t.quantity * t.purchase_price
        if t.trade_type == "sell":
            delta = -delta

        monthly[account_name][month_key] += delta

    # sort months globally
    all_months = sorted({
        m for acc in monthly.values() for m in acc.keys()
    })

    datasets = []

    for account_name, months in monthly.items():
        values = []
        running_total = Decimal("0.00")

        for m in all_months:
            running_total += months.get(m, Decimal("0.00"))
            values.append(float(running_total))

        datasets.append({
            "label": account_name,
            "values": values
        })

    return {
        "labels": all_months,
        "datasets": datasets
    }


@login_required
def dashboard(request):
    user = request.user
    assets = Asset.objects.filter(user=user).prefetch_related('price_history', 'trades')
    accounts = Account.objects.filter(user=user)

    # Build portfolio holdings
    holdings = []
    total_value = Decimal('0.00')
    total_cost = Decimal('0.00')

    portfolio_history = build_portfolio_history(user)

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

    for asset in assets:
        qty = asset.total_quantity(user=user)
        if qty <= 0:
            continue

        price = asset.current_price()
        if not price:
            price = Decimal('0.00')

        value = asset.total_value()
        cost = asset.cost_basis(user=user)
        gain = value - cost

        holdings.append({
            'portfolio_history_json': json.dumps(portfolio_history),
            'contribution_data_json': json.dumps(contribution_data),
            'asset': asset,
            'quantity': qty,
            'price': price,
            'value': value,
            'cost': cost,
            'gain': gain,
            'gain_pct': (gain / cost * 100) if cost > 0 else Decimal('0.00'),
        })
        total_value += value
        total_cost += cost
        
    total_gain = total_value - total_cost
    total_return = (
        ((total_value - total_cost) / total_cost * 100)
        if total_cost
        else 0
    )

    # Portfolio allocation pie chart data
    allocation_data = [
        {'label': h['asset'].ticker, 'value': float(h['value'])}
        for h in holdings
    ]

    # Per-account breakdown
    account_data = []
    for account in accounts:
        account_holdings = []
        account_value = Decimal('0.00')
        account_cost = Decimal('0.00')

        for asset in assets:
            qty = asset.account_quantity(account)
            if qty <= 0:
                continue

            price = asset.current_price()
            if not price:
                price = Decimal('0.00')

            value = asset.account_value(account)
            cost = asset.account_cost_basis(account)
            gain = value - cost

            account_holdings.append({
                'asset': asset,
                'quantity': qty,
                'price': price,
                'value': value,
                'cost': cost,
                'gain': gain,
            })
            account_value += value
            account_cost += cost

        account_data.append({
            'account': account,
            'holdings': account_holdings,
            'value': account_value,
            'cost': account_cost,
            'gain': account_value - account_cost,
            'room': account.remaining_room(),
            'status': account.room_status(),
        })

    account_value_history_json = build_account_value_history(user)

    context = {
        'holdings': holdings,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain': total_gain,
        'total_return': total_return,
        'account_value_history_json': account_value_history_json,

        # 🔥 THESE WERE MISSING
        'portfolio_history_json': json.dumps(portfolio_history),
        'contribution_data_json': json.dumps(contribution_data),

        'allocation_json': json.dumps(allocation_data),
        'account_data': account_data,
    }
    return render(request, 'tracker/dashboard.html', context)


def build_portfolio_history(user):
    assets = Asset.objects.filter(user=user).prefetch_related('price_history', 'trades')

    dates = sorted(
        set(
            AssetPriceHistory.objects
            .filter(asset__user=user)
            .values_list('date', flat=True)
        )
    )

    labels = []
    values = []

    for d in dates:
        total = Decimal('0.00')

        for asset in assets:
            price = (
                asset.price_history
                .filter(date__lte=d)
                .order_by('-date')
                .first()
            )
            if not price:
                continue

            qty = asset.total_quantity(user=user)
            total += price.price * qty

        labels.append(d.strftime('%Y-%m-%d'))
        values.append(float(total))

    return {
        'labels': labels,
        'values': values,
    }

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
    user = request.user
    assets = Asset.objects.filter(user=user).prefetch_related('price_history', 'trades')

    asset_data = []
    for asset in assets:
        qty = asset.total_quantity(user=user)
        if qty <= 0:
            continue

        price = asset.current_price()
        if not price:
            price = Decimal('0.00')

        value = asset.total_value()
        cost = asset.cost_basis(user=user)
        gain = value - cost

        asset_data.append({
            'asset': asset,
            'quantity': qty,
            'price': price,
            'value': value,
            'cost': cost,
            'gain': gain,
            'gain_pct': (gain / cost * 100) if cost > 0 else Decimal('0.00'),
        })

    return render(request, 'tracker/investments.html', {'asset_data': asset_data})


@login_required
def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.user = request.user
            asset.save()
            messages.success(request, 'Security added.')
            return redirect('asset_list')
    else:
        form = AssetForm()
    return render(request, 'tracker/asset_form.html', {'form': form, 'title': 'Add Security'})


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Security updated.')
            return redirect('asset_list')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'tracker/asset_form.html', {'form': form, 'title': 'Edit Security'})


@login_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Security deleted.')
        return redirect('asset_list')
    return render(request, 'tracker/confirm_delete.html', {'object': asset, 'object_type': 'Security'})


@login_required
def asset_price_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AssetPriceHistoryForm(request.POST)
        if form.is_valid():
            price_history = form.save(commit=False)
            price_history.asset = asset
            price_history.save()
            messages.success(request, 'Price updated.')
            return redirect('asset_list')
    else:
        form = AssetPriceHistoryForm(initial={'date': date.today()})
    return render(request, 'tracker/price_form.html', {'form': form, 'asset': asset})


@login_required
def trade_list(request):
    trades = Trade.objects.filter(user=request.user).select_related("asset", "account")

    account_type = request.GET.get("account_type")
    if account_type:
        trades = trades.filter(account__type=account_type)

    context = {
        "trades": trades,
        "selected_account_type": account_type,
        "account_types": ["TFSA", "RRSP", "FHSA", "LIRA", "Non-Registered"],
    }
    return render(request, "tracker/trades.html", context)


@login_required
def trade_create(request):
    if request.method == 'POST':
        form = TradeForm(user=request.user, data=request.POST)
        if form.is_valid():
            trade = form.save(commit=False)
            trade.user = request.user
            trade.year = trade.date.year
            trade.save()
            messages.success(request, 'Trade recorded.')
            return redirect('trade_list')
    else:
        form = TradeForm(user=request.user)
    return render(request, 'tracker/trade_form.html', {'form': form, 'title': 'Add Trade'})


@login_required
def trade_edit(request, pk):
    trade = get_object_or_404(Trade, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TradeForm(user=request.user, data=request.POST, instance=trade)
        if form.is_valid():
            trade = form.save(commit=False)
            trade.year = trade.date.year
            trade.save()
            messages.success(request, 'Trade updated.')
            return redirect('trade_list')
    else:
        form = TradeForm(user=request.user, instance=trade)
    return render(request, 'tracker/trade_form.html', {'form': form, 'title': 'Edit Trade'})


@login_required
def trade_delete(request, pk):
    trade = get_object_or_404(Trade, pk=pk, user=request.user)
    if request.method == 'POST':
        trade.delete()
        messages.success(request, 'Trade deleted.')
        return redirect('trade_list')
    return render(request, 'tracker/confirm_delete.html', {'object': trade, 'object_type': 'Trade'})
