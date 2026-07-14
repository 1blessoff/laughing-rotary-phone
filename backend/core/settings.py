from pathlib import Path
from dotenv import load_dotenv
import os
import ssl
import dj_database_url  # ← AJOUTER CET IMPORT


# NOTE (fix Avast/antivirus) :
# Cette ligne ne couvre QUE les appels via urllib/requests (contexte HTTPS
# par défaut). Elle N'A AUCUN EFFET sur l'envoi d'email SMTP, car depuis
# Django 4.2, EmailBackend construit son propre contexte SSL indépendamment
# de ce contexte par défaut. Le vrai fix pour l'email se trouve plus bas
# (voir la section EMAIL CONFIGURATION) via InsecureSMTPEmailBackend.
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'


# Forcer l'utilisation d'un bundle CA fiable (utile sous Windows/venv)
try:
    import certifi
    # Fix: définir SSL_CERT_FILE pour que OpenSSL utilise le cacert de certifi
    os.environ.setdefault('SSL_CERT_FILE', certifi.where())
except Exception:
    # Pas bloquant si certifi absent — laisser la configuration système
    pass

# ============================================
# CHARGER LES VARIABLES D'ENVIRONNEMENT
# ============================================
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# SECURITY
# ============================================
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("La variable SECRET_KEY n'est pas définie dans .env")

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ============================================
# APPLICATION DEFINITION
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ========== TIERS ==========
    'corsheaders',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'whitenoise',  # ← AJOUTÉ pour les fichiers statiques en production

    # ========== VOS APPLICATIONS ==========
    'audit.apps.AuditConfig',
    'authentication.apps.AuthenticationConfig',
    'terrains.apps.TerrainsConfig',
    'reservations.apps.ReservationsConfig',
    'concessions.apps.ConcessionsConfig',
    'finances.apps.FinancesConfig',
    'dashboard.apps.DashboardConfig',
    'flet_app.apps.FletAppConfig',
]

# ============================================
# MIDDLEWARE
# ============================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← AJOUTÉ (après SecurityMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# URLS & TEMPLATES
# ============================================
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ============================================
# DATABASE - PostgreSQL (avec support Render)
# ============================================

# Utiliser DATABASE_URL pour Render, ou fallback sur les variables individuelles
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=not DEBUG  # SSL en production uniquement
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', 'gestion_funeraire'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'options': '-c search_path=public',
            },
        }
    }

# ============================================
# AUTHENTIFICATION
# ============================================
AUTH_USER_MODEL = 'authentication.User'

# ============================================
# PASSWORD VALIDATION
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================
# INTERNATIONALIZATION
# ============================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Brazzaville'
USE_I18N = True
USE_TZ = True

# ============================================
# STATIC & MEDIA FILES
# ============================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuration de WhiteNoise pour la production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================
# EMAIL CONFIGURATION (depuis .env)
# ============================================

EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)

# Si EMAIL_HOST_USER est défini dans .env, on utilise SMTP (Gmail)
if os.getenv('EMAIL_HOST_USER'):
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@gestionfuneraire.com')

    # FIX : erreur "Basic Constraints of CA cert not marked critical",
    # causée par l'inspection SSL d'un antivirus (Avast, etc.) qui génère
    # de faux certificats mal formés, rejetés par OpenSSL 3.x.
    if os.getenv('EMAIL_SSL_VERIFY', 'True') == 'False':
        EMAIL_BACKEND = 'core.email_backend.InsecureSMTPEmailBackend'
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_TIMEOUT = 60

# ============================================
# GOOGLE AUTHENTICATOR (OTP)
# ============================================
OTP_TOTP_ISSUER = os.getenv('OTP_TOTP_ISSUER', 'GestionFuneraire')
OTP_TOTP_DIGITS = int(os.getenv('OTP_TOTP_DIGITS', 6))
OTP_TOTP_STEP = int(os.getenv('OTP_TOTP_STEP', 30))

# ============================================
# LOGGING
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'authentication': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# ============================================
# DEFAULT AUTO FIELD
# ============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# CORS CONFIGURATION
# ============================================

# En développement, autoriser toutes les origines
CORS_ALLOW_ALL_ORIGINS = DEBUG

if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:8000,http://127.0.0.1:8000'
    ).split(',')

# Ajouter les origines Render en production
if not DEBUG:
    CORS_ALLOWED_ORIGINS += [
        'https://*.onrender.com',
    ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = ['set-cookie']

# ============================================
# SESSION & CSRF
# ============================================

# En développement, désactiver HTTPS
if DEBUG:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Trusted Origins - Ajouter Render en production
if DEBUG:
    CSRF_TRUSTED_ORIGINS = os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'http://localhost:8000,http://127.0.0.1:8000'
    ).split(',')
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://*.onrender.com',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

# Durée de la session en secondes (1 heure)
SESSION_COOKIE_AGE = 3600

# Expiration de la session à la fermeture du navigateur
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ============================================
# SECURITY - Production (HTTPS, HSTS, etc.)
# ============================================

if not DEBUG:
    # Forcer HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Autres sécurités
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Cookies sécurisés
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

# ============================================
# SESSION & MFA CONFIGURATION
# ============================================

# Durée de validité du code MFA (en secondes) - 5 minutes
MFA_CODE_EXPIRATION = 300

# Durée de validité du code de réinitialisation (en secondes) - 15 minutes
RESET_CODE_EXPIRATION = 900

# ============================================
# SITE CONFIGURATION
# ============================================
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')