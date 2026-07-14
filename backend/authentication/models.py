from django.contrib.auth.models import AbstractUser
from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice

class User(AbstractUser):
    ROLE_CHOICES = (  

        ('admin', 'Administrateur'),
        ('agent', 'Agent de terrain'),
        ('secretariat', 'Secrétariat'),
        ('client', 'Client'),
    )
        
    
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_mfa_enabled = models.BooleanField(default=True)
    mfa_code = models.CharField(max_length=6, blank=True, null=True)
    mfa_code_created_at = models.DateTimeField(blank=True, null=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_totp_device(self):
        """Récupère ou crée un périphérique TOTP pour Google Authenticator"""
        device, created = TOTPDevice.objects.get_or_create(
            user=self,
            confirmed=False,
            name=f"Google Authenticator - {self.username}"
        )
        return device
    
    def has_totp_device(self):
        """Vérifie si l'utilisateur a un périphérique TOTP configuré"""
        return TOTPDevice.objects.filter(user=self, confirmed=True).exists()