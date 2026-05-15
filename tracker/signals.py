from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Asset, Contribution

def should_affect_contribution(asset):
    return asset.affects_contribution_room==True

@receiver(post_save, sender=Asset)
def create_contribution_on_asset_save(sender, instance, created, **kwargs):
    if not created:
        return

    purchase_value = instance.purchase_price * instance.quantity
    year = instance.purchase_date.year

    if should_affect_contribution(instance):
        Contribution.objects.create(
            user=instance.user,
            account=instance.account,
            year=instance.purchase_date.year,
            amount=instance.purchase_value(),
            auto_generated=True,
        )
