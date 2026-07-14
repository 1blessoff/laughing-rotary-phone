# main.py (ou app.py)
import flet as ft
from pages.dashboard_agent import agent_dashboard
from pages.dashboard_admin import admin_dashboard
from pages.dashboard_client import client_dashboard
from pages.dashboard_secretariat import secretariat_dashboard

from utils.session import session

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    # Simuler une session utilisateur (à supprimer en production)
    session.set("user", {
        "id": 1,
        "username": "sarah",
        "email": "admin@test.com",
        "role": "secretariat"  # ou "client"
    })
    
    # Rediriger directement vers le dashboard
    if session.get("user", {}).get("role") == "admin":
        admin_dashboard(page)
    elif session.get("user", {}).get("role") == "agent":
        agent_dashboard(page)
    elif session.get("user", {}).get("role") == "secretariat":
        secretariat_dashboard(page)
    else:
        client_dashboard(page)

ft.app(target=main)