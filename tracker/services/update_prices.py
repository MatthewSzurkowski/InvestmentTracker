import yfinance as yf
from decimal import Decimal
from datetime import date

from tracker.models import Asset, AssetValueHistory


def fetch_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")

        if hist.empty:
            return None

        return Decimal(str(hist["Close"].iloc[-1]))

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def update_asset_prices():
    assets = Asset.objects.exclude(ticker__isnull=True).exclude(ticker="")

    today = date.today()

    # 1. group assets by ticker
    grouped = {}

    for asset in assets:
        grouped.setdefault(asset.ticker.upper(), []).append(asset)

    # 2. fetch once per ticker
    prices = {}

    for ticker in grouped.keys():
        prices[ticker] = fetch_price(ticker)

    updated = 0

    # 3. apply to each asset
    for ticker, asset_list in grouped.items():
        price = prices.get(ticker)

        if price is None:
            continue

        for asset in asset_list:

            obj, created = AssetValueHistory.objects.update_or_create(
                asset=asset,
                date=today,
                defaults={
                    "value": price
                }
            )

            updated += 1

    print(f"Updated {updated} asset history rows")