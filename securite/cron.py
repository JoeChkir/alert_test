from django.core.management.base import BaseCommand
from django.utils import timezone
import os
from datetime import timedelta
from django.conf import settings 

class Command(BaseCommand):
    help = 'Nettoie les anciennes images temporaires'

    def handle(self, *args, **options):
        secure_dir = os.path.join(settings.MEDIA_ROOT, 'acces_secure')
        
        for filename in os.listdir(secure_dir):
            filepath = os.path.join(secure_dir, filename)
            creation_time = os.path.getctime(filepath)
            if (timezone.now() - timezone.datetime.fromtimestamp(creation_time)) > timedelta(hours=24):
                os.remove(filepath)