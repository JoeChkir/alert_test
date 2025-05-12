from celery import shared_task
from .gdpr_utils import purger_donnees
from celery import shared_task
from .models import AlerteAcces
from datetime import timezone
@shared_task
def purger_donnees():
    purger_donnees()

@shared_task
def purger_donnees():
    AlerteAcces.objects.filter(date_expiration__lt=timezone.now()).delete