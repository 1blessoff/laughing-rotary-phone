from django.db import models
from django.conf import settings
from reservations.models import Reservation
from datetime import datetime, timedelta

class Concession(models.Model):
    TYPE_CHOICES = (
        ('temporaire', 'Temporaire'),
        ('perpetuelle', 'Perpetuelle'),
    )
    
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='concession')
    type_concession = models.CharField(max_length=20, choices=TYPE_CHOICES, default='temporaire')
    date_debut = models.DateField()
    duree_ans = models.IntegerField(default=10, help_text="Duree en annees (0 = perpetuelle)")
    date_fin = models.DateField(null=True, blank=True)
    
    actif = models.BooleanField(default=True)
    renouvelable = models.BooleanField(default=True)
    date_renouvellement = models.DateField(null=True, blank=True)
    
    # Documents
    contrat_pdf = models.FileField(upload_to='concessions/contrats/', null=True, blank=True)
    numero_contrat = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Suivi
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Concession {self.numero_contrat} - {self.type_concession}"
    
    def est_expiree(self):
        if self.type_concession == 'perpetuelle':
            return False
        if self.date_fin and self.date_fin < datetime.now().date():
            return True
        return False
    
    def jours_restants(self):
        if self.type_concession == 'perpetuelle' or not self.date_fin:
            return None
        delta = self.date_fin - datetime.now().date()
        return max(0, delta.days)
    
    def renouveler(self, duree_ans=None):
        if self.type_concession == 'perpetuelle':
            return {"error": "Les concessions perpetuelles ne peuvent pas etre renouvelees"}
        
        if duree_ans:
            self.duree_ans = duree_ans
        
        if self.date_fin:
            self.date_fin = self.date_fin + timedelta(days=365 * self.duree_ans)
        else:
            self.date_fin = datetime.now().date() + timedelta(days=365 * self.duree_ans)
        
        self.date_renouvellement = datetime.now().date()
        self.actif = True
        self.save()
        
        return {"success": True, "new_date_fin": self.date_fin}


class Exhumation(models.Model):
    STATUT_CHOICES = (
        ('demande', 'Demande'),
        ('approuvee', 'Approuvee'),
        ('realisee', 'Realisee'),
        ('refusee', 'Refusee'),
    )
    
    concession = models.ForeignKey(Concession, on_delete=models.CASCADE, related_name='exhumations')
    demandeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='demande')
    
    motif = models.TextField()
    date_demande = models.DateTimeField(auto_now_add=True)
    date_approbation = models.DateTimeField(null=True, blank=True)
    date_realisation = models.DateTimeField(null=True, blank=True)
    
    # Documents legaux
    autorisation_pdf = models.FileField(upload_to='exhumations/autorisations/', null=True, blank=True)
    proces_verbal_pdf = models.FileField(upload_to='exhumations/pv/', null=True, blank=True)
    
    # Suivi
    approuve_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='exhumations_approuvees')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Exhumation {self.id} - {self.concession}"
    
    def approuver(self, utilisateur):
        self.statut = 'approuvee'
        self.date_approbation = datetime.now()
        self.approuve_par = utilisateur
        self.save()
        return True
    
    def realiser(self):
        self.statut = 'realisee'
        self.date_realisation = datetime.now()
        self.save()
        return True
    
    def refuser(self, utilisateur, motif=None):
        self.statut = 'refusee'
        if motif:
            self.notes = motif
        self.save()
        return True



    