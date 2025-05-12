# management/commands/purge_data.py
from django.core.management.base import BaseCommand
from securite.gdpr_utils import purger_donnees

class Command(BaseCommand):
    help = 'Purger les données expirées'

    def handle(self, *args, **options):
        purger_donnees()
        self.stdout.write(self.style.SUCCESS('Purge des données terminée'))
