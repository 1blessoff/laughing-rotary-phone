# backend/create_superuser.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Remplacez par vos identifiants
username = "bless"
email = "koukachrist48@gmail.com"
password = "bless1234"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superutilisateur '{username}' créé avec succès !")
else:
    print(f"ℹ️ Le superutilisateur '{username}' existe déjà.")