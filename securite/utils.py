# securite/utils.py
from django.core.mail import send_mail
from twilio.rest import Client
import cv2
import pyautogui
from .models import AlerteAcces,  Agent, PersonneAutorisee
from django.utils import timezone
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from twilio.rest import Client
import pyshorteners
from django.conf import settings 
import numpy as np
from PIL import Image
import shutil
import logging
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)


"""""
SMTP_SERVER = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 25
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
EMAIL_FROM = "towihi3172@noroasis.com"
EMAIL_TO = "mipoje1144@exclussi.com"

# --- Paramètres Twilio ---
#TWILIO_SID = ""
#TWILIO_AUTH_TOKEN = ""
#TWILIO_PHONE = ""
#RECIPIENT_PHONE = ""
"""
SMTP_SERVER = getattr(settings, "EMAIL_HOST", "sandbox.smtp.mailtrap.io")
SMTP_PORT = getattr(settings, "EMAIL_PORT", 587)
SMTP_USERNAME = getattr(settings, "EMAIL_HOST_USER", "")
SMTP_PASSWORD = getattr(settings, "EMAIL_HOST_PASSWORD", "")
EMAIL_FROM = getattr(settings, "DEFAULT_FROM_EMAIL", "security@example.com")

# Paramètres Twilio (à configurer dans settings.py)
#TWILIO_SID = getattr(settings, "TWILIO_ACCOUNT_SID", "")
#TWILIO_AUTH_TOKEN = getattr(settings, "TWILIO_AUTH_TOKEN", "")
#TWILIO_PHONE = getattr(settings, "TWILIO_PHONE_NUMBER", "")

def shorten_url(long_url):
    try:
        s = pyshorteners.Shortener()
        return s.tinyurl.short(long_url)
    except Exception as e:
        print(f"Erreur de raccourcissement d'URL : {e}")
        return long_url 


def send_email_alert(subject, message, vector_data=None, alert_id=None):
    """
    Version RGPD-compatible pour l'envoi d'alertes par email
    Args:
        subject (str): Sujet de l'email
        message (str): Corps du message
        vector_data (bytes, optional): Données vectorielles anonymisées
        alert_id (int, optional): ID de l'alerte pour référence
    """
    agents = Agent.objects.filter(recoit_email=True)
    if not agents.exists():
        logger.warning("Aucun agent configuré pour recevoir des emails")
        return False

    for agent in agents:
        try:
            # Configuration du message
            msg = MIMEMultipart()
            msg["From"] = EMAIL_FROM
            msg["To"] = agent.email
            msg["Subject"] = f"[ALERTE {alert_id}] {subject}" if alert_id else subject

            # Construction du corps du message
            body = f"""
            {message}
            
            Détails techniques :
            - ID Alerte : {alert_id or 'N/A'}
            - Données vectorielles : {"Disponibles" if vector_data else "Non disponibles"}
            - Confidentialité : Données RGPD-compatibles (floutage + vectorisation)
            """
            msg.attach(MIMEText(body, "plain"))

            # Ajout des données vectorielles en pièce jointe sécurisée
            if vector_data:
                try:
                    vector_part = MIMEApplication(vector_data, Name=f"alert_{alert_id}_vector.bin")
                    vector_part['Content-Disposition'] = f'attachment; filename="alert_{alert_id}_secure_data.bin"'
                    msg.attach(vector_part)
                except Exception as e:
                    logger.error(f"Erreur attachement vectoriel : {e}")

            # Envoi sécurisé
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email d'alerte envoyé à {agent.email} (Alerte ID: {alert_id})")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"Erreur SMTP pour {agent.email}: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue pour {agent.email}: {e}")
    
    return False



def send_sms_alert(message, image_url=None):
    """
    Envoie une alerte SMS à tous les agents qui acceptent les SMS
    """
    agents = Agent.objects.filter(recoit_sms=True).exclude(telephone__isnull=True).exclude(telephone__exact='')
    #                                 ^^^^^^^^^^ Utilisez le nom correct du champ
    if not agents.exists():
        print("Aucun agent avec numéro valide configuré pour recevoir des SMS")
        return False

    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    
    for agent in agents:
        try:
            # Préparation du message
            full_message = message
            if image_url:
                short_url = shorten_url(image_url)
                full_message = f"{message}\n📷 Image : {short_url}"

            # Envoi du SMS
            client.messages.create(
                body=full_message,
                from_=TWILIO_PHONE,
                to=agent.telephone  # <-- Utilisez agent.telephone au lieu de agent.phone
            )
            print(f"📱 SMS envoyé avec succès à {agent.telephone}")
            
        except Exception as e:
            print(f"❌ Erreur d'envoi de SMS à {agent.telephone} : {e}")
            continue
    
    return True


""""        
def envoyer_email_alerte(ip, tentative):
    send_mail(
        subject='🚨 Alerte tentative d’accès',
        message=f'Tentative: {tentative}\nIP: {ip}',
        from_email='youssefsk.chkir@gmail.com',  # Doit correspondre à celui de settings.py
        recipient_list=['admin@exemple.com'],   # Mets ici ton vrai mail
    )

def envoyer_sms(ip, tentative):
    account_sid = 'sid'  # Remplace par ton SID Twilio
    auth_token = 'token'  # Remplace par ton Token Twilio
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"🚨 Alerte tentative: {tentative} IP: {ip}",
        from_='+numreoo',  # Ton numéro Twilio
        to='+numero'    # Le numéro du destinataire (admin ou autre)
    )
"""
def capturer_intrus(nom_fichier='intrus.jpg'):
    """Capture une image depuis la webcam"""
    camera = cv2.VideoCapture(0)
    return_value, image = camera.read()
    cv2.imwrite(f'media/intrus/{nom_fichier}', image)
    camera.release()
    return f'intrus/{nom_fichier}'

def capture_ecran(nom_fichier='intrus.jpg'):
    """Capture l'écran"""
    screenshot = pyautogui.screenshot()
    screenshot.save(f'media/intrus/{nom_fichier}')
    return f'intrus/{nom_fichier}'

def enregistrer_alerte(image_path, statut="intrus", confiance=95.0, details=""):
    """
    Enregistre une nouvelle alerte
    """
    # Générer un nom de fichier unique
    nom_fichier = f"intrus_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg"
    nouveau_chemin = f"intrus_detectes/{nom_fichier}"
    
    # Copier l'image dans le bon dossier
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'intrus_detectes'), exist_ok=True)
    shutil.copy(image_path, os.path.join(settings.MEDIA_ROOT, nouveau_chemin))
    
    # Créer l'alerte
    alerte = AlerteAcces.objects.create(
        nom="Détection automatique",
        statut=statut,
        confiance=confiance,
        image=nouveau_chemin,
        details=details
    )
    
    # Envoyer les alertes si intrus
    if statut == 'intrus':
        image_url = f"{settings.SITE_URL}{settings.MEDIA_URL}{nouveau_chemin}"
        message = f"🚨 INTRUS DÉTECTÉ!\n\nDate: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n"
        message += f"Confiance: {confiance}%\nImage: {image_url}"
        
        send_sms_alert(message)
        send_email_alert("ALERTE INTRUS", message, os.path.join(settings.MEDIA_ROOT, nouveau_chemin), image_url)
    
    return alerte
    
    # Envoi des alertes par email et SMS
    #envoyer_email_alerte(ip, tentative)
    #envoyer_sms(ip, tentative)


def analyser_images_intrus():
    dossier_intrus = os.path.join(settings.MEDIA_ROOT, 'intrus')
    
    for fichier in os.listdir(dossier_intrus):
        chemin_complet = os.path.join(dossier_intrus, fichier)
        
        if os.path.isfile(chemin_complet) and fichier.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Extraire le nom sans extension
            nom_fichier = os.path.splitext(fichier)[0]
            
            if 'intrus' in fichier.lower():
                statut = 'intrus'
                confiance = 90.0
            elif 'acces_non_autorise' in fichier.lower():
                statut = 'acces_non_autorise'
                confiance = 60.0
            else:
                statut = 'acces_autorise'
                confiance = 10.0
            
            if not AlerteAcces.objects.filter(image=f'intrus/{fichier}').exists():
                alerte = AlerteAcces.objects.create(
                    nom=nom_fichier,  # Utilisation du nom du fichier
                    statut=statut,
                    confiance=confiance,
                    image=f'intrus/{fichier}'
                )
                
                # Envoi automatique pour les intrus
                if statut == 'intrus':
                    image_url = f"{settings.SITE_URL}{settings.MEDIA_URL}intrus/{fichier}"
                    if send_sms_alert("🚨 INTRUS DÉTECTÉ !", image_url):
                        alerte.action_prise = 'sms'
                    if send_email_alert("🔴 Alerte Intrusion", "Un intrus a été détecté", chemin_complet, image_url):
                        alerte.action_prise = 'email' if alerte.action_prise == 'none' else 'sms+email'
                    alerte.date_action = timezone.now()
                    alerte.save()


def comparer_images(image1_path, image2_path, seuil=30):
    """Compare deux images avec un seuil de similarité"""
    try:
        # Charger les images
        img1 = cv2.imread(image1_path)
        img2 = cv2.imread(image2_path)
        
        if img1 is None or img2 is None:
            return False
            
        # Redimensionner si nécessaire
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Calculer la différence absolue
        difference = cv2.absdiff(img1, img2)
        gray = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
        
        # Calculer le pourcentage de similarité
        non_zero = cv2.countNonZero(threshold)
        total_pixels = gray.shape[0] * gray.shape[1]
        similarity = (total_pixels - non_zero) / total_pixels * 100
        
        return similarity > seuil
    except Exception as e:
        print(f"Erreur comparaison images: {e}")
        return False

def detecter_intrus(image_path, seuil_similarite=30):
    """
    Compare l'image avec celles du dossier autorisés
    """
    dossier_autorises = os.path.join(settings.MEDIA_ROOT, 'autorises')
    
    # Si pas d'images autorisées, tout est intrus
    if not os.path.exists(dossier_autorises) or not os.listdir(dossier_autorises):
        return True
    
    # Charger l'image à tester
    img_test = cv2.imread(image_path)
    if img_test is None:
        return True
    
    for fichier in os.listdir(dossier_autorises):
        if fichier.lower().endswith(('.png', '.jpg', '.jpeg')):
            chemin_autorise = os.path.join(dossier_autorises, fichier)
            img_autorise = cv2.imread(chemin_autorise)
            
            if img_autorise is None:
                continue
                
            # Redimensionner pour comparaison
            img_test_resized = cv2.resize(img_test, (img_autorise.shape[1], img_autorise.shape[0]))
            
            # Calculer la similarité (méthode simple)
            diff = cv2.absdiff(img_autorise, img_test_resized)
            similarity = np.mean(diff)
            
            if similarity < seuil_similarite:  # Plus c'est bas, plus c'est similaire
                return False  # Personne autorisée trouvée
    
    return True

def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')