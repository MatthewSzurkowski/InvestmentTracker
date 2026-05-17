from celery import shared_task
from tracker.services.update_prices import update_asset_prices
from forex_python.converter import CurrencyRates
from decimal import Decimal
from .models import FXRate

@shared_task
def refresh_asset_prices():
    update_asset_prices()

@shared_task
def update_usd_cad_rate():
    c = CurrencyRates()
    usd_rate = Decimal(str(c.convert("USD", "CAD", 1)))

    FXRate.objects.update_or_create(
        pair="USD_CAD",
        defaults={"rate": usd_rate}
    )

    cad_rate = Decimal(str(c.convert("USD", "CAD", 1)))

    FXRate.objects.update_or_create(
        pair="CAD_USD",
        defaults={"rate": cad_rate}
    )