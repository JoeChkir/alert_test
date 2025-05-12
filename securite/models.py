# securite/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
import os
from django.contrib.auth.models import User
import logging

def default_expiration_date():
    """Date d'expiration par défaut (30 jours)"""
    return timezone.now() + timedelta(days=30)

logger = logging.getLogger(__name__)

def anonymiser_vecteur(vecteur):
    """Fonction d'anonymisation des données biométriques"""
    # Implémentation de l'anonymisation
    # (à compléter selon vos besoins spécifiques)
    return vecteur

class AlerteAcces(models.Model):
    STATUT_CHOICES = [
        ('intrus', 'Intrus détecté'),
        ('acces_non_autorise', 'Accès non autorisé'),
        ('acces_autorise', 'Accès autorisé'),
        ('pending', 'En attente de traitement'),
        ('expire', 'Données expirées'),
    ]
    
    # Identifiants
    nom = models.CharField(
        max_length=100, 
        default="Inconnu",
        verbose_name="Identifiant alerte"
    )
    
    # Métadonnées
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage création"
    )
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES,
        default='pending',
        verbose_name="Niveau de menace"
    )
    confiance = models.FloatField(
        default=0.0,
        verbose_name="Niveau de confiance (%)",
        help_text="Probabilité estimée de la menace (0-100%)"
    )
    
    # Données techniques
    vecteur_visage = models.BinaryField(
        null=True,
        blank=True,
        verbose_name="Empreinte biométrique sécurisée",
        help_text="Vecteur flouté et réduit (32x32px)"
    )
    
    metadata = models.JSONField(
        default=dict,
        verbose_name="Métadonnées techniques",
        help_text="Données contextuelles non-identifiantes"
    )
    
    # Gestion RGPD
    date_expiration = models.DateTimeField(
        default=default_expiration_date,
        verbose_name="Date d'expiration RGPD"
    )
    est_anonyme = models.BooleanField(
        default=True,
        verbose_name="Anonymisation validée"
    )
    hash_securise = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Hash anonyme",
        help_text="SHA256 des données vectorielles"
    )
    
    # Audit
    action_prise = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Action de sécurité"
    )
    date_action = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Dernière action"
    )

    class Meta:
        verbose_name = "Alerte sécurisée"
        verbose_name_plural = "Alertes sécurisées"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"ALERT-{self.id} [{self.get_statut_display()}] {self.confiance}%"

    def save(self, *args, **kwargs):
        if self.vecteur_visage and not self.est_anonyme:
            self.vecteur_visage = anonymiser_vecteur(self.vecteur_visage)
            self.est_anonyme = True
        super().save(*args, **kwargs)

    def est_valide(self):
        """Vérifie si l'alerte est toujours valide (non expirée)"""
        return self.date_expiration > timezone.now()

    @property
    def delai_restant(self):
        """Retourne le délai restant avant expiration"""
        return self.date_expiration - timezone.now()

class IntrusImage(models.Model):
    image = models.ImageField(
        upload_to='intrus/',
        blank=True, 
        null=True,
        verbose_name="Image de l'intrus"
    )
    description = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Description"
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )
    
    class Meta:
        verbose_name = "Image d'intrus"
        verbose_name_plural = "Images d'intrus"
    
    def __str__(self):
        return f"Intrus Image {self.id} - {self.description or 'Sans description'}"

class TentativeIntrusion(models.Model):
    nom = models.CharField(
        max_length=100, 
        default='Inconnu',
        verbose_name="Nom de l'intrus"
    )
    datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date et heure"
    )
    confiance = models.FloatField(
        default=0.0,
        verbose_name="Niveau de confiance"
    )
    statut = models.CharField(
        max_length=100, 
        default='en_attente',
        verbose_name="Statut"
    )
    capture = models.ImageField(
        upload_to='alertes/',
        null=True,
        blank=True,
        verbose_name="Capture de l'intrus"
    )
    
    class Meta:
        verbose_name = "Tentative d'intrusion"
        verbose_name_plural = "Tentatives d'intrusion"
        ordering = ['-datetime']
    
    def __str__(self):
        return f"{self.nom} - {self.datetime.strftime('%d/%m/%Y %H:%M')}"

class Agent(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Utilisateur associé"
    )
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom complet"
    )
    email = models.EmailField(
        verbose_name="Adresse email"
    )
    telephone = models.CharField(
        max_length=20,
        verbose_name="Numéro de téléphone"
    )
    recoit_sms = models.BooleanField(
        default=False,
        verbose_name="Reçoit les SMS d'alerte"
    )
    recoit_email = models.BooleanField(
        default=True,
        verbose_name="Reçoit les emails d'alerte"
    )
    
    class Meta:
        verbose_name = "Agent de sécurité"
        verbose_name_plural = "Agents de sécurité"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.email})"
    
    @property
    def nom_complet(self):
        return self.nom.strip()

class PersonneAutorisee(models.Model):
    nom = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nom complet"
    )
    image = models.ImageField(
        upload_to='personnes_autorisees/',
        verbose_name="Photo de référence"
    )
    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )
    date_expiration = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Date d'expiration"
    )
    
    class Meta:
        verbose_name = "Personne autorisée"
        verbose_name_plural = "Personnes autorisées"
        ordering = ['nom']
    
    def save(self, *args, **kwargs):
        if not self.date_expiration:
            self.date_expiration = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nom