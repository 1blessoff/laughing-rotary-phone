from django.db import models

class CategorieCaveau(models.Model):
    nom = models.CharField(max_length=100)
    largeur = models.DecimalField(max_digits=6, decimal_places=2)
    longueur = models.DecimalField(max_digits=6, decimal_places=2)
    prix_base = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.nom

class Caveau(models.Model):
    STATUT_CHOICES = (
        ('disponible', 'Disponible'),
        ('reserve', 'Réservé'),
        ('occupe', 'Occupé'),
        ('non_exploitable', 'Non exploitable'),
    )
    
    reference = models.CharField(max_length=50, unique=True)
    categorie = models.ForeignKey(CategorieCaveau, on_delete=models.PROTECT, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')
    
    # Coordonnées GPS
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude GPS")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude GPS")
    
    # Informations de localisation
    section = models.CharField(max_length=10)
    bloc = models.CharField(max_length=10, blank=True)
    allee = models.CharField(max_length=10, blank=True)
    superficie = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Informations du propriétaire (si occupé)
    proprietaire_nom = models.CharField(max_length=200, blank=True)
    proprietaire_contact = models.CharField(max_length=20, blank=True)
    
    # Suivi
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    historique_statut = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.reference} - {self.get_statut_display()}"
    
    def changer_statut(self, nouveau_statut, utilisateur):
        """Change le statut et enregistre dans l'historique"""
        ancien_statut = self.statut
        self.statut = nouveau_statut
        
        # Ajouter à l'historique
        historique = self.historique_statut or []
        historique.append({
            'ancien': ancien_statut,
            'nouveau': nouveau_statut,
            'utilisateur': str(utilisateur),
            'date': str(self.date_modification)
        })
        self.historique_statut = historique
        self.save()
    
    def get_statut_color(self):
        """Retourne la couleur associée au statut"""
        Colors = {
            'disponible': 'green',
            'reserve': 'orange',
            'occupe': 'red',
            'non_exploitable': 'gray'
        }
        return Colors.get(self.statut, 'gray')
    
    @property
    def est_disponible(self):
        return self.statut == 'disponible'
    
    @property
    def est_reserve(self):
        return self.statut == 'reserve'
    
    @property
    def est_occupe(self):
        return self.statut == 'occupe'