#frontend/pages/dashboard.py

import flet as ft
from utils.session import session

def dashboard_page(page: ft.Page):
    """Redirige vers le dashboard du role de l'utilisateur"""
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    role = user.get("role", "client")
    
    if role == "admin":
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)
    elif role == "agent":
        from pages.dashboard_agent import agent_dashboard
        agent_dashboard(page)
    elif role == "secretariat":
        from pages.dashboard_secretariat import secretariat_dashboard
        secretariat_dashboard(page)
    else:
        from pages.dashboard_client import client_dashboard
        client_dashboard(page)