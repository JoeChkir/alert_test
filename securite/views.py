# securite/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import AlerteAcces, TentativeIntrusion, Agent, PersonneAutorisee
from .forms import AgentCreationForm, AgentForm
from .utils import (
    send_sms_alert,
    send_email_alert,
    capturer_intrus,
    capture_ecran,
    enregistrer_alerte,
    analyser_images_intrus,
    detecter_intrus 
)
from PIL import Image
import os
from datetime import datetime
from django.db.models import Count, Q
from django.http import JsonResponse
from .gdpr_utils import image_to_vector, anonymiser_image, purger_donnees, image_to_secure_vector
import tempfile
from datetime import timedelta
from django.http import JsonResponse
from django.http import JsonResponse, HttpResponseNotAllowed
import json
import logging
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
import cv2
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
import shortuuid
from twilio.rest import Client 
import random

#purger_donnees()
# Décorateur pour vérifier les droits admin
def admin_required(user):
    return user.is_superuser

# securite/views.py
from django.shortcuts import render

def biometrie_info(request):
    return render(request, 'securite/biometrie_info.html')

def consentement_form(request):
    # Logique du formulaire de consentement
    return render(request, 'securite/consentement_form.html')
@user_passes_test(admin_required)
def dashboard(request):
    # Récupération des données de base
    agents = Agent.objects.all().order_by('nom')
    alertes = AlerteAcces.objects.order_by('-date')[:10]
    personnes_autorisees = PersonneAutorisee.objects.all()
    
    # Calcul des statistiques
    aujourd_hui = datetime.now().date()
    debut_semaine = aujourd_hui - timedelta(days=7)
    
    # Données RGPD à suivre
    donnees_rgpd = [
        {
            'nom': 'Données biométriques',
            'type': 'RGPD Art.9', 
            'anonymise': AlerteAcces.objects.filter(est_anonyme=False).count() == 0,
            'total': AlerteAcces.objects.count(),
            'non_anonymes': AlerteAcces.objects.filter(est_anonyme=False).count()
        },
        {
            'nom': 'Journaux accès',
            'type': 'RGPD Art.30',
            'anonymise': True,
            'total': AlerteAcces.objects.count(),
            'non_anonymes': 0
        },
        {
            'nom': 'Coordonnées agents',
            'type': 'RGPD Art.6',
            'anonymise': False,
            'total': Agent.objects.count(),
            'non_anonymes': Agent.objects.count()
        }
    ]
    
    # Calcul des alertes récentes
    alertes_recentes = {
        '24h': AlerteAcces.objects.filter(date__gte=aujourd_hui).count(),
        '7j': AlerteAcces.objects.filter(date__gte=debut_semaine).count(),
        'intrus': AlerteAcces.objects.filter(statut='intrus').count(),
        'en_attente': AlerteAcces.objects.filter(statut='pending').count()
    }
    
    context = {
        # Données principales
        'agents': agents,
        'alertes': alertes,
        'personnes_autorisees': personnes_autorisees,
        
        # Conformité RGPD
        'donnees_rgpd': donnees_rgpd,
        'pourcentage_conformite': int((sum(1 for d in donnees_rgpd if d['anonymise']) / len(donnees_rgpd)) * 100),
        
        # Statistiques
        'stats': {
            'total_alertes': AlerteAcces.objects.count(),
            'alertes_recentes': alertes_recentes,
            'agents_actifs': Agent.objects.filter(recoit_email=True).count(),
            'personnes_autorisees': personnes_autorisees.count(),
            'prochaines_expirations': PersonneAutorisee.objects.filter(
                date_expiration__lte=aujourd_hui + timedelta(days=7)
            ).count()
        },
        
        # Métadonnées
        'last_update': datetime.now(),
        'periode_couverture': f"{debut_semaine.strftime('%d/%m/%Y')} - {aujourd_hui.strftime('%d/%m/%Y')}"
    }
    
    return render(request, 'securite/dashboard.html', context)

@user_passes_test(admin_required)
@require_POST
def gerer_alerte(request, alerte_id):
    print("Données POST complètes:", request.POST)  # Debug crucial
    
    alerte = get_object_or_404(AlerteAcces, id=alerte_id)
    action = request.POST.get('action')
    
    if not action:
        messages.error(request, "Erreur technique: Aucune action spécifiée")
        print("ERREUR: Aucune action dans:", request.POST)  # Debug
        return redirect('dashboard')

    try:
        if action == 'email':
            send_email_alert(
                subject=f"⚠️ Alerte {alerte.statut}",
                message=f"Confiance: {alerte.confiance}%",
                vector_data=alerte.vecteur_visage,
                alert_id=alerte.id
            )
            alerte.action_prise = 'email'
            messages.success(request, "Email envoyé avec succès")
            
        elif action == 'sms':
            send_sms_alert(f"Alerte {alerte.statut} (ID: {alerte.id})")
            alerte.action_prise = 'sms'
            messages.success(request, "SMS envoyé avec succès")
            
        alerte.save()
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        print("ERREUR:", str(e))  # Debug

    return redirect('dashboard')# Redirection vers le dashboard unifié

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)
 # À retirer en production après les tests
@require_http_methods(["GET", "POST"])  # Temporaire pour le debug
def enregistrer_consentement(request):
    if request.method == 'POST':
        request.session['consentement_capture'] = True
        return JsonResponse({'status': 'success'})
    return HttpResponseNotAllowed(['POST'])

def biometrie_info(request):
    """Nouvelle vue pour la page d'information sur la biométrie"""
    return render(request, 'securite/biometrie_info.html')

# Vue de test (uniquement pour le développement)
@csrf_exempt
def test_consent(request):
    return render(request, 'securite/test_consent.html')
# Gestion des agents
@user_passes_test(admin_required)
def liste_agents(request):
    agents = Agent.objects.all().order_by('nom')
    return render(request, 'securite/liste_agents.html', {'agents': agents})

@user_passes_test(admin_required)
def creer_agent(request):
    if request.method == 'POST':
        form = AgentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Agent créé avec succès")
            return redirect('liste_agents')
    else:
        form = AgentForm()
    return render(request, 'securite/creer_agent.html', {'form': form})

@user_passes_test(admin_required)
def modifier_agent(request, id):
    agent = get_object_or_404(Agent, id=id)
    if request.method == 'POST':
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "Agent modifié avec succès")
            return redirect('liste_agents')
    else:
        form = AgentForm(instance=agent)
    return render(request, 'securite/modifier_agent.html', {'form': form})

@user_passes_test(admin_required)
def supprimer_agent(request, id):
    agent = get_object_or_404(Agent, id=id)
    if request.method == 'POST':
        agent.delete()
        messages.success(request, "Agent supprimé avec succès")
        return redirect('liste_agents')
    return render(request, 'securite/confirmer_suppression.html', {'agent': agent})

# Fonctions pour la détection d'intrusion
@user_passes_test(admin_required)
def tentative_intrusion(request):
    """Simule une tentative d'intrusion avec capture d'image"""
    filename = f'intrus/intrus_{datetime.now().strftime("%Y%m%d%H%M%S")}.jpg'
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Création d'une image de test
    image = Image.new('RGB', (640, 480), color='red')
    image.save(file_path)
    
    # Création de l'alerte
    alerte = AlerteAcces.objects.create(
        nom="Intrus Simulé",
        statut='intrus',
        confiance=95.0,
        image=filename
    )
    
    # Envoi des alertes
    image_url = f"{settings.SITE_URL}{settings.MEDIA_URL}{filename}"
    send_email_alert(
        "🚨 INTRUS DÉTECTÉ (Test)",
        "Une intrusion a été détectée lors d'un test système.",
        file_path,
        image_url
    )
    
    return render(request, 'securite/tentative_intrusion.html', {
        'file_path': filename,
        'alerte': alerte
    })

@user_passes_test(admin_required)
def liste_alertes(request):
    """Liste complète des alertes"""
    alertes = AlerteAcces.objects.all().order_by('-date')
    return render(request, 'securite/liste_alertes.html', {'alertes': alertes})

# API Endpoints
def get_alertes(request):
    """Endpoint API pour les alertes (JSON)"""
    alertes = AlerteAcces.objects.all().order_by('-date')
    data = [{
        "id": a.id,
        "nom": a.nom,
        "date": a.date.strftime("%Y-%m-%d %H:%M:%S"),
        "confiance": a.confiance,
        "statut": a.statut,
        "image_url": a.image.url if a.image else None,
        "action_prise": a.action_prise
    } for a in alertes]
    return JsonResponse(data, safe=False)

def vue_image_intrus(request, filename):
    """Retourne l'image des intrus"""
    file_path = os.path.join(settings.MEDIA_ROOT, 'intrus', filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
    return HttpResponse("Image non trouvée", status=404)
def envoyer_alertes_intrus(alerte, image_path, request=None):
    if request:
        base_url = f"{request.scheme}://{request.get_host()}"
    else:
        base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
    
    token = shortuuid.uuid()[:8]
    image_url = f"{base_url}/media/{image_path}?token={token}"
    
    envoyer_email_alerte(alerte, image_url)
    envoyer_sms_alerte(alerte, image_url)

def generate_short_url(original_url):
    # Ici vous utiliseriez un service comme Bitly ou votre propre solution
    # Ceci est une solution simplifiée pour l'exemple
    token = shortuuid.uuid()[:8]
    return f"{settings.BASE_URL}/i/{token}"

def envoyer_email_alerte(alerte, image_url):
    subject = f"🚨 Alerte intrus - Confiance: {alerte.confiance}%"
    
    context = {
        'alerte': alerte,
        'image_url': image_url,
        'duree_validite': '30 minutes'
    }
    
    html_message = render_to_string('securite/email_alerte.html', context)
    plain_message = f"""
    Alerte intrus. Confiance: {alerte.confiance}%
    Détails techniques :
    - ID Alerte : {alerte.id}
    - Image : {image_url} (valide 30min)
    - Confidentialité : Données RGPD-compatibles
    """
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [agent.email for agent in Agent.objects.filter(recoit_email=True)],
        html_message=html_message
    )


def envoyer_sms_alerte(alerte, image_url):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        for agent in Agent.objects.filter(recoit_sms=True):
            message = client.messages.create(
                body=f"⚠️ Alerte intrus (ID: {alerte.id}) - {image_url}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=agent.telephone
            )
    except Exception as e:
        logger.error(f"Erreur envoi SMS: {str(e)}")

@user_passes_test(admin_required)
def envoyer_alerte(request, alerte_id):
    """Alias pour gerer_alerte (pour compatibilité avec les URLs existantes)"""
    return gerer_alerte(request, alerte_id)

def envoyer_alertes(alerte):
    # Envoyer email
    sujet = f"🚨 Alerte Intrus - Confiance: {alerte.confiance}%"
    message = f"""
    Alerte de sécurité :
    - Type: {alerte.nom}
    - Confiance: {alerte.confiance}%
    - Date: {alerte.date}
    """
    
    agents = Agent.objects.filter(recoit_email=True)
    send_mail(
        sujet,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [agent.email for agent in agents],
        fail_silently=False
    )
    
    # Envoyer SMS
    if hasattr(settings, 'TWILIO_ACCOUNT_SID'):
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        for agent in Agent.objects.filter(recoit_sms=True):
            client.messages.create(
                body=f"⚠️ Alerte Intrus (Confiance: {alerte.confiance}%)",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=agent.telephone
            )

@user_passes_test(admin_required)
@csrf_exempt
def detection_temps_reel(request):
    if request.method == 'POST':
        # Simuler la détection (75% de chance de détection)
        if random.random() < 0.75:
            alerte = AlerteAcces.objects.create(
                nom="Intrus détecté",
                confiance=round(random.uniform(80.0, 99.9), 1),
                statut='intrus'
            )
            
            # Envoyer les alertes
            envoyer_alertes(alerte)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Intrus détecté ! Alertes envoyées.',
                'confidence': alerte.confiance,
                'alert_id': alerte.id
            })
        return JsonResponse({
            'status': 'success',
            'message': 'Aucun intrus détecté'
        })
    
    return render(request, 'securite/detection_temps_reel.html')
    
    # Cas normal (pas d'intrus)


@user_passes_test(admin_required)
def ajouter_autorise(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        image_file = request.FILES.get('image')
        
        if nom and image_file:
            # Sauvegarder l'image
            filename = f"autorise_{nom}.jpg"
            filepath = os.path.join('personnes_autorisees', filename)
            
            with open(os.path.join(settings.MEDIA_ROOT, filepath), 'wb+') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            # Créer l'entrée dans la base
            PersonneAutorisee.objects.create(
                nom=nom,
                image=filepath
            )
            messages.success(request, f"Personne {nom} ajoutée avec succès")
            
    return redirect('dashboard')
# securite/views.py
from django.views.decorators.csrf import csrf_exempt
import tempfile

@csrf_exempt
def capture_secure(request):
    """Capture RGPD-compatible avec consentement"""
    if request.method == 'POST':
        # Vérifier le consentement (stocké en session ou base de données)
        if not request.session.get('consentement_capture', False):
            return JsonResponse({'status': 'error', 'message': 'Consentement requis'}, status=403)

        # Capture depuis la webcam
        camera = cv2.VideoCapture(0)
        _, frame = camera.read()
        camera.release()

        # Sauvegarde temporaire (mémoire uniquement)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp:
            cv2.imwrite(tmp.name, frame)
            
            # Conversion RGPD (floutage + vectorisation)
            vector = image_to_secure_vector(tmp.name)  # Utilisez votre fonction existante

            # Enregistrement sécurisé
            AlerteAcces.objects.create(
                nom="Capture sécurisée",
                vecteur_visage=vector,
                statut='pending',
                date_expiration=timezone.now() + timedelta(days=1)  # Suppression après 24h
            )

        return JsonResponse({'status': 'success'})
    return HttpResponseNotAllowed(['POST'])

# Vue publique
def home(request):
    """Page d'accueil publique"""
    return render(request, 'securite/home.html')