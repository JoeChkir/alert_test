"""
URL configuration for alert_test project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for alert_test project.
"""
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from securite import views as securite_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    
    path('', securite_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('alertes/', securite_views.liste_alertes, name='liste_alertes'),
    path('tentative-intrusion/', securite_views.tentative_intrusion, name='tentative_intrusion'),
    path('tentative-intrusion/image', securite_views.vue_image_intrus, name='image_intrus'),
    path('dashboard/', securite_views.dashboard, name='dashboard'),
    path('alertes-json/', securite_views.get_alertes, name='alertes_json'),
    path('gerer-alerte/<int:alerte_id>/', securite_views.gerer_alerte, name='gerer_alerte'),
    path('agents/', securite_views.liste_agents, name='liste_agents'),
    path('agents/creer/', securite_views.creer_agent, name='creer_agent'),
    path('agents/modifier/<int:id>/', securite_views.modifier_agent, name='modifier_agent'),
    path('agents/supprimer/<int:id>/', securite_views.supprimer_agent, name='supprimer_agent'),
    path('envoyer-alerte/<int:alerte_id>/', securite_views.gerer_alerte, name='envoyer_alerte'),
    path('detection/', securite_views.detection_temps_reel, name='detection_temps_reel'),
    path('consentement/', securite_views.consentement_form, name='consentement_form'), 
    path('biometrie-info/', securite_views.biometrie_info, name='biometrie_info'), 
    path('enregistrer-consentement/', securite_views.enregistrer_consentement, name='enregistrer_consentement'), #to correct voir le fichier pour corriger.png et essaye pour corriger l'errue ecrit 
    path('test-consentement/', csrf_exempt(securite_views.test_consent), name='test_consentement'),     # Uniquement pour le développement
    path('ajouter-autorise/', securite_views.ajouter_autorise, name='ajouter_autorise'),
    path('capture-secure/', securite_views.capture_secure, name='capture_secure'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 