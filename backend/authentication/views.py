from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from ninja import Router, Schema
from datetime import timedelta
from typing import Optional 
import random
import string
import os  # <-- AJOUTÉ pour debug

User = get_user_model()
auth_router = Router()

# ============================================
# ENVOI EMAIL AVEC LOGS DÉTAILLÉS
# ============================================

def send_mail_async(subject, message, recipient_list):
    """
    Envoie l'email de façon SYNCHRONE avec logs détaillés.
    """
    print("=" * 60)
    print("📧 send_mail_async - DEBUT")
    print(f"📧 Subject: {subject}")
    print(f"📧 Recipient: {recipient_list}")
    
    # === LOGS DES VARIABLES D'ENVIRONNEMENT ===
    print("\n--- VARIABLES D'ENVIRONNEMENT ---")
    email_host = os.getenv('EMAIL_HOST', 'NON DEFINI')
    email_port = os.getenv('EMAIL_PORT', 'NON DEFINI')
    email_user = os.getenv('EMAIL_HOST_USER', 'NON DEFINI')
    email_password = os.getenv('EMAIL_HOST_PASSWORD', 'NON DEFINI')
    email_from = os.getenv('DEFAULT_FROM_EMAIL', 'NON DEFINI')
    
    print(f"📧 EMAIL_HOST: {email_host}")
    print(f"📧 EMAIL_PORT: {email_port}")
    print(f"📧 EMAIL_HOST_USER: {email_user}")
    print(f"📧 EMAIL_HOST_PASSWORD: {'OK (défini)' if email_password != 'NON DEFINI' else 'MANQUANT !'}")
    print(f"📧 DEFAULT_FROM_EMAIL: {email_from}")
    
    # === LOGS DES SETTINGS DJANGO ===
    print("\n--- SETTINGS DJANGO ---")
    try:
        print(f"📧 settings.EMAIL_HOST: {settings.EMAIL_HOST}")
    except AttributeError:
        print("📧 settings.EMAIL_HOST: NON DEFINI")
    try:
        print(f"📧 settings.EMAIL_PORT: {settings.EMAIL_PORT}")
    except AttributeError:
        print("📧 settings.EMAIL_PORT: NON DEFINI")
    try:
        print(f"📧 settings.EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    except AttributeError:
        print("📧 settings.EMAIL_HOST_USER: NON DEFINI")
    try:
        print(f"📧 settings.EMAIL_HOST_PASSWORD: {'OK' if settings.EMAIL_HOST_PASSWORD else 'VIDE'}")
    except AttributeError:
        print("📧 settings.EMAIL_HOST_PASSWORD: NON DEFINI")
    try:
        print(f"📧 settings.DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    except AttributeError:
        print("📧 settings.DEFAULT_FROM_EMAIL: NON DEFINI")
    try:
        print(f"📧 settings.EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    except AttributeError:
        print("📧 settings.EMAIL_BACKEND: NON DEFINI")
    
    # === TENTATIVE D'ENVOI ===
    print("\n--- TENTATIVE D'ENVOI ---")
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print(f"✅ Email envoye avec succes a {recipient_list}")
    except Exception as e:
        print(f"❌ ERREUR EMAIL: {e}")
        print(f"❌ Type d'erreur: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
    
    print("📧 send_mail_async - FIN")
    print("=" * 60)


# ============================================
# SCHEMAS
# ============================================

class RegisterSchema(Schema):
    username: str
    email: str
    password: str
    password2: str
    role: str = "client"
    phone: str = None

class LoginSchema(Schema):
    username: str
    password: str

class MFASchema(Schema):
    mfa_code: str
    user_id: int

class PasswordResetSchema(Schema):
    email: str

class PasswordResetConfirmSchema(Schema):
    email: str
    code: str
    new_password: str

class ToggleMFASchema(Schema):
    enabled: bool

class UpdateProfileSchema(Schema):
    username: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


# ============================================
# 1. INSCRIPTION
# ============================================

@auth_router.post("/register")
def register(request, data: RegisterSchema):
    """Inscription d'un nouvel utilisateur"""
    print("=" * 60)
    print("=== register ===")
    print(f"Username: {data.username}")
    print(f"Email: {data.email}")
    
    if data.password != data.password2:
        return {"error": "Les mots de passe ne correspondent pas"}
    
    if User.objects.filter(username=data.username).exists():
        return {"error": "Ce nom d'utilisateur existe deja"}
    
    if User.objects.filter(email=data.email).exists():
        return {"error": "Cet email existe deja"}
    
    user = User.objects.create(
        username=data.username,
        email=data.email,
        password=make_password(data.password),
        role=data.role,
        phone=data.phone,
        is_active=True,
        is_mfa_enabled=True,
    )
    
    print(f"✅ Utilisateur cree: {user.username} ({user.role})")
    print("=" * 60)
    
    return {
        "success": True,
        "message": "Inscription reussie ! Veuillez vous connecter.",
        "redirect": "/login",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
    }


# ============================================
# 2. CONNEXION → MFA obligatoire
# ============================================

@auth_router.post("/login")
def login_user(request, data: LoginSchema):
    """Connexion utilisateur avec MFA par email"""
    
    print("=" * 60)
    print("=== login_user ===")
    print(f"Username: {data.username}")
    
    user = authenticate(request, username=data.username, password=data.password)
    
    if user is None:
        print("❌ Identifiants invalides")
        print("=" * 60)
        return {"error": "Identifiants invalides"}
    
    if not user.is_active:
        print(f"❌ Compte desactive: {user.username}")
        print("=" * 60)
        return {"error": "Ce compte est desactive. Contactez l'administrateur."}
    
    code = ''.join(random.choices(string.digits, k=6))
    user.mfa_code = code
    user.mfa_code_created_at = timezone.now()
    user.save()
    
    print(f"✅ Code MFA genere pour {user.username}: {code}")
    
    request.session['mfa_user_id'] = user.id
    
    # Envoi email avec logs
    print("\n--- ENVOI DU CODE MFA ---")
    send_mail_async(
        subject="Code de verification - Gestion Funeraire",
        message=f"""
Bonjour {user.username},

Votre code de verification est : {code}

Ce code est valable 5 minutes.

Si vous n'etes pas a l'origine de cette demande, ignorez cet email.
""",
        recipient_list=[user.email],
    )
    
    print("=" * 60)
    
    return {
        "success": True,
        "message": "Code MFA envoye par email",
        "requires_mfa": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
    }


@auth_router.post("/verify-mfa")
def verify_mfa(request, data: MFASchema):
    """Verification du code MFA"""
    
    print("=" * 60)
    print("=== verify_mfa ===")
    print(f"user_id recu: {data.user_id}")
    print(f"code recu: {data.mfa_code}")
    
    user_id = data.user_id
    
    if not user_id:
        print("❌ ID utilisateur manquant")
        print("=" * 60)
        return {"error": "ID utilisateur manquant"}
    
    try:
        user = User.objects.get(id=user_id)
        print(f"✅ Utilisateur trouve: {user.username} ({user.role})")
    except User.DoesNotExist:
        print(f"❌ Utilisateur introuvable: id={user_id}")
        print("=" * 60)
        return {"error": "Utilisateur introuvable"}
    
    if user.mfa_code != data.mfa_code:
        print(f"❌ Code MFA invalide: attendu={user.mfa_code}, recu={data.mfa_code}")
        print("=" * 60)
        return {"error": "Code MFA invalide"}
    
    if user.mfa_code_created_at and (timezone.now() - user.mfa_code_created_at) > timedelta(minutes=5):
        print(f"❌ Code MFA expire: cree a {user.mfa_code_created_at}")
        print("=" * 60)
        return {"error": "Le code MFA a expire. Veuillez vous reconnecter."}
    
    user.mfa_code = None
    user.mfa_code_created_at = None
    user.save()
    
    login(request, user)
    print(f"✅ Utilisateur connecte: {user.username} ({user.role})")
    print("=" * 60)
    
    return {
        "success": True,
        "message": "Connexion reussie",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
    }


# ============================================
# 3. DECONNEXION
# ============================================

@auth_router.post("/logout")
def logout_user(request):
    """Deconnexion"""
    print(f"=== logout_user: {request.user}")
    logout(request)
    return {"success": True, "message": "Deconnecte avec succes"}


# ============================================
# 4. PROFIL UTILISATEUR
# ============================================

@auth_router.put("/update-profile")
def update_profile(request, data: UpdateProfileSchema):
    """Mettre à jour le profil de l'utilisateur"""
    print("=" * 60)
    print("=== update_profile ===")
    
    if not request.user.is_authenticated:
        print("❌ Non authentifie")
        print("=" * 60)
        return {"error": "Non authentifie"}
    
    user = request.user
    print(f"👤 Utilisateur: {user.username}")
    
    # Mettre à jour le username si fourni
    if data.username is not None and data.username != "":
        if User.objects.filter(username=data.username).exclude(id=user.id).exists():
            return {"error": "Ce nom d'utilisateur est deja pris"}
        user.username = data.username
        print(f"✅ Username mis a jour: {data.username}")
    
    # Mettre à jour le téléphone si fourni
    if data.phone is not None:
        user.phone = data.phone
        print(f"✅ Phone mis a jour: {data.phone}")
    
    # Mettre à jour le mot de passe si fourni
    if data.password and data.password != "":
        user.password = make_password(data.password)
        print("✅ Mot de passe mis a jour")
    
    user.save()
    
    print("=" * 60)
    
    return {
        "success": True,
        "message": "Profil mis à jour avec succès",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
        }
    }


@auth_router.get("/me")
def get_current_user(request):
    """Recuperer l'utilisateur connecte"""
    print("=" * 60)
    print("=== get_current_user ===")
    
    if not request.user.is_authenticated:
        print("❌ Non authentifie")
        print("=" * 60)
        return {"error": "Non authentifie"}
    
    user = request.user
    print(f"✅ Utilisateur: {user.username} ({user.role})")
    print("=" * 60)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "phone": user.phone,
        "is_active": user.is_active,
        "last_login": user.last_login,
        "is_mfa_enabled": user.is_mfa_enabled,
    }


# ============================================
# 5. MOT DE PASSE OUBLIE
# ============================================

@auth_router.post("/request-password-reset")
def request_password_reset(request, data: PasswordResetSchema):
    """Demander une reinitialisation de mot de passe"""
    print("=" * 60)
    print("=== request_password_reset ===")
    print(f"📧 Email: {data.email}")
    
    try:
        user = User.objects.get(email=data.email)
        print(f"✅ Utilisateur trouve: {user.username}")
    except User.DoesNotExist:
        print(f"❌ Email non trouve: {data.email}")
        print("=" * 60)
        return {"error": "Aucun compte avec cet email"}
    
    code = ''.join(random.choices(string.digits, k=6))
    user.mfa_code = code
    user.mfa_code_created_at = timezone.now()
    user.save()
    
    print(f"✅ Code genere: {code}")
    
    send_mail_async(
        subject="Reinitialisation du mot de passe - Gestion Funeraire",
        message=f"""
Bonjour {user.username},

Vous avez demande la reinitialisation de votre mot de passe.

Votre code de reinitialisation est : {code}

Ce code est valable 15 minutes.

Si vous n'avez pas demande cette reinitialisation, ignorez cet email.
""",
        recipient_list=[user.email],
    )
    
    print("=" * 60)
    
    return {
        "success": True,
        "message": "Email de reinitialisation envoye"
    }


@auth_router.post("/confirm-password-reset")
def confirm_password_reset(request, data: PasswordResetConfirmSchema):
    """Confirmer la reinitialisation du mot de passe"""
    print("=" * 60)
    print("=== confirm_password_reset ===")
    print(f"📧 Email: {data.email}")
    
    try:
        user = User.objects.get(email=data.email)
        print(f"✅ Utilisateur trouve: {user.username}")
    except User.DoesNotExist:
        print("❌ Aucun compte avec cet email")
        print("=" * 60)
        return {"error": "Aucun compte avec cet email"}
    
    if user.mfa_code != data.code:
        print(f"❌ Code invalide: attendu={user.mfa_code}, recu={data.code}")
        print("=" * 60)
        return {"error": "Code invalide"}
    
    if user.mfa_code_created_at and (timezone.now() - user.mfa_code_created_at) > timedelta(minutes=15):
        print(f"❌ Code expire: cree a {user.mfa_code_created_at}")
        print("=" * 60)
        return {"error": "Le code a expire. Veuillez refaire une demande."}
    
    user.password = make_password(data.new_password)
    user.mfa_code = None
    user.mfa_code_created_at = None
    user.save()
    
    print(f"✅ Mot de passe reinitialise pour {user.username}")
    print("=" * 60)
    
    return {
        "success": True,
        "message": "Mot de passe reinitialise avec succes. Veuillez vous connecter."
    }


# ============================================
# 6. ADMIN - GESTION DES UTILISATEURS
# ============================================

@auth_router.get("/users")
def get_users(request):
    """Liste des utilisateurs (Admin/Secretariat)"""
    print("=" * 60)
    print("=== get_users ===")
    
    if not request.user.is_authenticated:
        print("❌ Non authentifie")
        print("=" * 60)
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'secretariat']:
        print(f"❌ Permission refusee pour {request.user.role}")
        print("=" * 60)
        return {"error": "Permission refusee"}
    
    users = User.objects.all().order_by('-date_joined')
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        })
    
    print(f"✅ {len(result)} utilisateurs trouves")
    print("=" * 60)
    return result


@auth_router.put("/users/{user_id}/role")
def change_user_role(request, user_id: int, role: str):
    """Changer le role d'un utilisateur (Admin seulement)"""
    print("=" * 60)
    print("=== change_user_role ===")
    print(f"👤 User ID: {user_id}")
    print(f"📋 Nouveau role: {role}")
    
    if not request.user.is_authenticated:
        print("❌ Non authentifie")
        print("=" * 60)
        return {"error": "Non authentifie"}
    
    if request.user.role != 'admin':
        print(f"❌ Permission refusee pour {request.user.role}")
        print("=" * 60)
        return {"error": "Permission refusee"}
    
    user = get_object_or_404(User, id=user_id)
    allowed_roles = ['admin', 'agent', 'secretariat', 'client']
    
    if role not in allowed_roles:
        print(f"❌ Role invalide: {role}")
        print("=" * 60)
        return {"error": f"Role invalide. Choisir parmi: {', '.join(allowed_roles)}"}
    
    user.role = role
    user.save()
    
    print(f"✅ Role de {user.username} change en {role}")
    print("=" * 60)
    
    return {
        "success": True,
        "message": f"Role de {user.username} change en {role}"
    }


@auth_router.put("/users/{user_id}/activate")
def toggle_user_active(request, user_id: int):
    """Activer/Desactiver un utilisateur (Admin seulement)"""
    print("=" * 60)
    print("=== toggle_user_active ===")
    print(f"👤 User ID: {user_id}")
    
    if not request.user.is_authenticated:
        print("❌ Non authentifie")
        print("=" * 60)
        return {"error": "Non authentifie"}
    
    if request.user.role != 'admin':
        print(f"❌ Permission refusee pour {request.user.role}")
        print("=" * 60)
        return {"error": "Permission refusee"}
    
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    print(f"✅ Compte {user.username} {'active' if user.is_active else 'desactive'}")
    print("=" * 60)
    
    return {
        "success": True,
        "message": f"Compte {user.username} {'active' if user.is_active else 'desactive'}"
    }


@auth_router.put("/toggle-mfa")
def toggle_mfa(request, data: ToggleMFASchema):
    """Activer/Desactiver le MFA"""
    print("=" * 60)
    print("=== toggle_mfa ===")
    print(f"📋 MFA enabled: {data.enabled}")
    
    if not request.user.is_authenticated:
        print("❌ Non authentifie")
        print("=" * 60)
        return {"error": "Non authentifie"}
    
    user = request.user
    user.is_mfa_enabled = data.enabled
    user.save()
    
    print(f"MFA {'active' if user.is_mfa_enabled else 'desactive'} pour {user.username}")
    
    
    return {
        "success": True,
        "message": f"MFA {'active' if user.is_mfa_enabled else 'desactive'}",
        "is_mfa_enabled": user.is_mfa_enabled,
    }