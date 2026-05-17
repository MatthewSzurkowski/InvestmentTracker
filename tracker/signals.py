from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Trade


@receiver(post_save, sender=Trade)
def update_contributions_on_trade_save(sender, instance, created, **kwargs):
    pass


@receiver(post_delete, sender=Trade)
def update_contributions_on_trade_delete(sender, instance, **kwargs):
    pass
