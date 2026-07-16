 # backend/create_superuser.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Récupérer depuis les variables d'environnement
username = os.getenv('ADMIN_USERNAME', 'bless')
email = os.getenv('ADMIN_EMAIL', 'koukachrist48@gmail.com')
password = os.getenv('ADMIN_PASSWORD')

if not password:
    raise ValueError("ADMIN_PASSWORD n'est pas défini dans les variables d'environnement !")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superutilisateur '{username}' créé avec succès !")
else:
    print(f"Le superutilisateur '{username}' existe déjà.")