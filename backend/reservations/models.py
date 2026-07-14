from django.db import models
from django.conf import settings
from terrains.models import Caveau
from datetime import datetime

class Reservation(models.Model):
    STATUT_CHOICES = (
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('annulee', 'Annulée'),
        ('refusee', 'Refusée'),
    )
    
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    caveau = models.ForeignKey(Caveau, on_delete=models.PROTECT, related_name='reservations')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    
    # Informations du défunt
    nom_defunt = models.CharField(max_length=200)
    prenom_defunt = models.CharField(max_length=200, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    date_deces = models.DateField()
    date_enterrement = models.DateField()
    
    # Informations de la famille
    nom_famille = models.CharField(max_length=200, blank=True)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email_contact = models.EmailField(blank=True)
    
    # Informations supplémentaires
    notes = models.TextField(blank=True)
    besoin_ceremonie = models.BooleanField(default=False, help_text="Besoin d'une cérémonie")
    besoin_voiture = models.BooleanField(default=False, help_text="Besoin de voiture funéraire")
    
    # Suivi
    date_reservation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_annulation = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations_validees')
    
    # Documents
    facture_pdf = models.FileField(upload_to='factures/', null=True, blank=True)
    certificat_pdf = models.FileField(upload_to='certificats/', null=True, blank=True)
    
    def __str__(self):
        return f"Réservation #{self.id} - {self.nom_defunt} ({self.get_statut_display()})"
    
    def get_statut_color(self):
        Colors = {
            'en_attente': 'orange',
            'validee': 'green',
            'annulee': 'red',
            'refusee': 'red',
        }
        return Colors.get(self.statut, 'gray')
    
    def valider(self, utilisateur):
        """Valider la réservation"""
        self.statut = 'validee'
        self.date_validation = datetime.now()
        self.valide_par = utilisateur
        self.save()
        
        # Changer le statut du caveau en 'occupe'
        self.caveau.changer_statut('occupe', utilisateur)
        
        return True
    
    def refuser(self, utilisateur):
        """Refuser la réservation"""
        self.statut = 'refusee'
        self.date_annulation = datetime.now()
        self.save()
        
        # Remettre le caveau en 'disponible'
        self.caveau.changer_statut('disponible', utilisateur)
        
        return True
    
    def annuler(self, utilisateur):
        """Annuler la réservation"""
        self.statut = 'annulee'
        self.date_annulation = datetime.now()
        self.save()
        
        # Remettre le caveau en 'disponible'
        self.caveau.changer_statut('disponible', utilisateur)
        
        return True