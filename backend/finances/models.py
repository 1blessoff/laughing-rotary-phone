from django.db import models
from reservations.models import Reservation
from django.conf import settings
from datetime import datetime

class Paiement(models.Model):
    METHODE_CHOICES = (
        ('airtel_money', 'Airtel Money'),
        ('mtn_money', 'MTN Mobile Money'),
        ('moov_money', 'Moov Money'),
        ('monex', 'Monex'),
        ('carte', 'Carte bancaire'),
        ('especes', 'Espèces'),
        ('virement', 'Virement'),
    )
    
    STATUT_CHOICES = (
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('echoue', 'Échoué'),
        ('rembourse', 'Remboursé'),
    )
    
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    methode = models.CharField(max_length=20, choices=METHODE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    
    date_paiement = models.DateTimeField(auto_now_add=True)
    reference_transaction = models.CharField(max_length=100, unique=True)
    est_partiel = models.BooleanField(default=False)
    solde_restant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Suivi
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Pour les paiements mobiles
    numero_transaction = models.CharField(max_length=50, blank=True)
    operateur = models.CharField(max_length=50, blank=True, help_text="Orange Money, Airtel Money, MTN Money, Moov Money, etc.")
    numero_telephone = models.CharField(max_length=20, blank=True)
    
    # Facture PDF
    facture_pdf = models.FileField(upload_to='factures/', null=True, blank=True)
    facture_generee_le = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Paiement {self.reference_transaction} - {self.montant} FCFA"
    
    def valider(self, utilisateur):
        self.statut = 'valide'
        self.date_validation = datetime.now()
        self.valide_par = utilisateur
        self.save()
        return True
    
    def est_complet(self):
        """Verifie si le paiement est complet (pas de solde restant)"""
        return self.solde_restant == 0
    
    def get_methode_display(self):
        return dict(self.METHODE_CHOICES).get(self.methode, self.methode)