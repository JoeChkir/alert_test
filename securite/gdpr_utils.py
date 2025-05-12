import cv2
import numpy as np
from datetime import timedelta
from django.utils import timezone
from .models import PersonneAutorisee, AlerteAcces
import os
import logging  # Importez le module logging directement

# Créez un logger spécifique pour ce module
logger = logging.getLogger(__name__)


def image_to_vector(image_path):
    """Convertit une image en vecteur simplifié sans reconnaissance faciale"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (100, 100))  # Réduction de dimension
    vecteur = img.flatten()  # Conversion en vecteur 1D
    return vecteur.tobytes()  # Retourne des bytes pour stockage

def anonymiser_image(image_path):
    """Floute fortement une image"""
    img = cv2.imread(image_path)
    img = cv2.GaussianBlur(img, (99, 99), 30)
    cv2.imwrite(image_path, img)
    return image_path
# securite/gdpr_utils.py
def anonymiser_vecteur(vector_data):
    """Applique un floutage supplémentaire aux données vectorielles"""
    vector = np.frombuffer(vector_data, dtype=np.float32)
    vector = vector * 0.9 + np.random.normal(0, 0.1, vector.shape)  # Bruitage
    return vector.tobytes()

def purger_donnees():
    from .models import PersonneAutorisee, AlerteAcces
    from django.utils import timezone
    
    # Purge personnes autorisées
    personnes_expirees = PersonneAutorisee.objects.filter(
        date_expiration__isnull=False,
        date_expiration__lt=timezone.now()
    )
    personnes_expirees.delete()
    
    # Purge alertes
    alertes_a_purger = AlerteAcces.objects.filter(
        date_suppression__isnull=False,
        date_suppression__lt=timezone.now()
    )
    for alerte in alertes_a_purger:
        if alerte.image:
            try:
                os.remove(alerte.image.path)
            except:
                pass
    alertes_a_purger.delete()
import cv2
import numpy as np

def image_to_secure_vector(image_path):
    """Version robuste de la conversion d'image"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Impossible de lire l'image capturée")
            
        # Floutage important
        img = cv2.GaussianBlur(img, (99, 99), 30)
        
        # Réduction drastique de la résolution
        img = cv2.resize(img, (32, 32))
        
        # Conversion en vecteur
        vector = img.flatten() / 255.0
        
        return vector.tobytes()
    except Exception as e:
        logger.error(f"Erreur conversion image: {str(e)}")
        raise