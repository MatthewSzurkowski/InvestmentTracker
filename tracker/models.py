from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('TFSA', 'TFSA'),
        ('RRSP', 'RRSP'),
        ('FHSA', 'FHSA'),
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
        return self.contributions.filter(year=self.year).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=20, blank=True, null=True)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=4)
    quantity = models.DecimalField(max_digits=16, decimal_places=6)

    class Meta:
        ordering = ['-purchase_date', 'name']

    def __str__(self):
        return f"{self.name} ({self.ticker or 'N/A'}) - {self.account}"

    def purchase_value(self):
        return self.purchase_price * self.quantity

    def current_value(self):
        latest = self.value_history.order_by('-date').first()
        if latest:
            return latest.value * self.quantity
        return self.purchase_value()

    def gain_loss(self):
        return self.current_value() - self.purchase_value()

    def gain_loss_pct(self):
        cost = self.purchase_value()
        if cost == 0:
            return Decimal('0.00')
        return (self.gain_loss() / cost) * 100


class Contribution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='contributions')
    year = models.IntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    auto_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account.type} {self.year} - ${self.amount}"


class AssetValueHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='value_history')
    date = models.DateField()
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        ordering = ['-date']
        unique_together = ('asset', 'date')

    def __str__(self):
        return f"{self.asset.name} on {self.date}: ${self.value}"
