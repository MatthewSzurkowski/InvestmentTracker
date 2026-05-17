from decimal import Decimal
from django.apps import apps


def get_rate(pair: str):
    """
    Safely fetch FX rate from DB without circular imports.
    """
    FXRate = apps.get_model("tracker", "FXRate")

    try:
        return FXRate.objects.get(pair=pair).rate
    except FXRate.DoesNotExist:
        return None


def usd_to_cad(amount: Decimal) -> Decimal:
    rate = get_rate("USD_CAD")

    if rate is None:
        return amount  # fallback (no conversion)

    return amount * rate


def cad_to_usd(amount: Decimal) -> Decimal:
    rate = get_rate("CAD_USD")

    if rate is None:
        return amount  # fallback (no conversion)

    return amount * rate