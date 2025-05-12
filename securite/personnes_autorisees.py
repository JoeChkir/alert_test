# securite/personnes_autorisees.py
import os
from django.core.files import File
from django.conf import settings
from .models import PersonneAutorisee

def ajouter_personne_autorisee(nom, image_file):
    """
    Ajoute une personne autorisée au système
    """
    # Créer le dossier si inexistant
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'personnes_autorisees'), exist_ok=True)
    
    # Enregistrer l'image
    filename = f"autorise_{nom.lower().replace(' ', '_')}.jpg"
    filepath = os.path.join('personnes_autorisees', filename)
    
    with open(os.path.join(settings.MEDIA_ROOT, filepath), 'wb+') as f:
        for chunk in image_file.chunks():
            f.write(chunk)
    
    # Ajouter à la base de données
    PersonneAutorisee.objects.create(
        nom=nom,
        image=filepath
    )