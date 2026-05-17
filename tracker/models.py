from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from decimal import Decimal
from tracker.fx import usd_to_cad


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('TFSA', 'TFSA'),
        ('RRSP', 'RRSP'),
        ('FHSA', 'FHSA'),
        ('LIRA', 'LIRA'),
        ('Non-Registered', 'Non-Registered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    year = models.IntegerField()
    annual_contribution_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        unique_together = ('user', 'type', 'year')
        ordering = ['-year', 'type']

    def __str__(self):
        return f"{self.type} ({self.year}) - {self.user.username}"

    def total_contributions(self):
        trades = Trade.objects.filter(account=self, year=self.year, trade_type='buy', affects_contribution_room=True)
        total = trades.aggregate(
            total=Sum(models.F('quantity') * models.F('purchase_price'), output_field=models.DecimalField())
        )['total'] or Decimal('0.00')
        return total

    def remaining_room(self):
        return self.annual_contribution_limit - self.total_contributions()

    def room_status(self):
        remaining = self.remaining_room()
        if remaining > 0:
            return 'green'
        elif remaining == 0:
            return 'grey'
        return 'red'


class Asset(models.Model):
    ASSET_TYPES = [
        ('ETF', 'ETF'),
        ('Stock', 'Stock'),
        ('Crypto', 'Crypto'),
        ('Other', 'Other'),
    ]

    CURRENCY_CHOICES = [
        ('CAD', 'CAD'),
        ('USD', 'USD'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=20, unique=True)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CAD')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ticker']

    def __str__(self):
        return f"{self.name} ({self.ticker})"

    def current_price(self):
        latest = self.price_history.order_by('-date').first()
        return latest.price if latest else None

    def total_quantity(self, user=None):
        trades = Trade.objects.filter(asset=self)
        if user:
            trades = trades.filter(user=user)
        buy_qty = trades.filter(trade_type='buy').aggregate(q=Sum('quantity'))['q'] or Decimal('0')
        sell_qty = trades.filter(trade_type='sell').aggregate(q=Sum('quantity'))['q'] or Decimal('0')
        return buy_qty - sell_qty

    def account_quantity(self, account):
        trades = Trade.objects.filter(asset=self, account=account)
        buy_qty = trades.filter(trade_type='buy').aggregate(q=Sum('quantity'))['q'] or Decimal('0')
        sell_qty = trades.filter(trade_type='sell').aggregate(q=Sum('quantity'))['q'] or Decimal('0')
        return buy_qty - sell_qty

    def total_value(self, user=None):
        price = self.current_price()
        if not price:
            return Decimal('0.00')
        qty = self.total_quantity(user=user)
        if self.currency=="USD":
            return qty * usd_to_cad(price)
        return price * qty
    

    def account_value(self, account):
        price = self.current_price()
        if not price:
            return Decimal('0.00')
        qty = self.account_quantity(account)
        if self.currency=="USD":
            return qty * usd_to_cad(price)
        return price * qty

    def cost_basis(self, user=None):
        buy_trades = Trade.objects.filter(asset=self, trade_type='buy')
        sell_trades = Trade.objects.filter(asset=self, trade_type='sell')

        if user:
            buy_trades = buy_trades.filter(user=user)
            sell_trades = sell_trades.filter(user=user)

        buy_total = buy_trades.aggregate(
            total=Sum(models.F('quantity') * models.F('purchase_price'))
        )['total'] or Decimal('0.00')

        sell_total = sell_trades.aggregate(
            total=Sum(models.F('quantity') * models.F('purchase_price'))
        )['total'] or Decimal('0.00')

        net = buy_total - sell_total

        # FX conversion (same rule as total_value)
        if self.currency == "USD":
            return usd_to_cad(net)

        return net

    def account_cost_basis(self, account):
        buy_trades = Trade.objects.filter(
            asset=self,
            account=account,
            trade_type='buy'
        )

        sell_trades = Trade.objects.filter(
            asset=self,
            account=account,
            trade_type='sell'
        )

        buy_total = buy_trades.aggregate(
            total=Sum(models.F('quantity') * models.F('purchase_price'))
        )['total'] or Decimal('0.00')

        sell_total = sell_trades.aggregate(
            total=Sum(models.F('quantity') * models.F('purchase_price'))
        )['total'] or Decimal('0.00')

        net = buy_total - sell_total

        # FX conversion (same rule as global cost_basis)
        if self.currency == "USD":
            return usd_to_cad(net)

        return net


class Trade(models.Model):
    TRADE_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='trades')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='trades')
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    quantity = models.DecimalField(max_digits=16, decimal_places=6)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=4)
    date = models.DateField()
    year = models.IntegerField()

    affects_contribution_room = models.BooleanField(
        null=True,
        help_text="If false, this asset does not affect contribution room"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.trade_type.upper()} {self.quantity} {self.asset.ticker} @ ${self.purchase_price}  - Counts to contribution: {self.affects_contribution_room}"

    def current_value(self):
        price = self.asset.current_price()
        if not price:
            return Decimal('0.00')
        if self.asset.currency=="USD":
            return self.quantity * usd_to_cad(price)
        return self.quantity * price
    
    def purchase_value(self):
        return self.purchase_price * self.quantity
    
    def asset_price(self):
        return self.asset.current_price()
    
    def gain_loss(self):
        return self.current_value() - self.purchase_value()

    def gain_loss_pct(self):
        cost = self.purchase_value()
        if cost == 0:
            return Decimal('0.00')
        return (self.gain_loss() / cost) * 100
    
    def book_cost(self):
        return self.quantity * self.purchase_price


class AssetPriceHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='price_history')
    date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        ordering = ['-date']
        unique_together = ('asset', 'date')

    def __str__(self):
        return f"{self.asset.ticker} on {self.date}: ${self.price}"

class FXRate(models.Model):
    pair = models.CharField(max_length=10, unique=True)  
    rate = models.DecimalField(max_digits=12, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['pair']

    def __str__(self):
        return f"{self.pair}: {self.rate}"