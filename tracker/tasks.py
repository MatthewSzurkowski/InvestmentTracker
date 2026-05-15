from celery import shared_task
from tracker.services.update_prices import update_asset_prices

@shared_task
def refresh_asset_prices():
    update_asset_prices()