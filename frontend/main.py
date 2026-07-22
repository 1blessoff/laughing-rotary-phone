import os
import atexit
import asyncio
import flet as ft

from pages.auth import login_page, register_page, mfa_page, forgot_password_page
from pages.dashboard_admin import admin_dashboard
from pages.dashboard_agent import agent_dashboard
from pages.dashboard_client import client_dashboard
from pages.dashboard_secretariat import secretariat_dashboard
from utils.session import session
from utils.api import close_session


def main(page: ft.Page):
    page.title = "Gestion Funéraire"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 600
    page.window_height = 960

    # NAVIGATION

    def go_to_login():
        page.route = "/login"
        page.update()
        login_page(page)

    def go_to_register():
        page.route = "/register"
        page.update()
        register_page(page)

    def go_to_mfa():
        page.route = "/mfa"
        page.update()
        mfa_page(page)

    def go_to_forgot_password():
        page.route = "/forgot-password"
        page.update()
        forgot_password_page(page)

    def go_to_dashboard():
        page.route = "/dashboard"
        page.update()
        user = session.get("user")
        if not user:
            go_to_login()
            return
        role = user.get("role", "client")
        if role == "admin":
            admin_dashboard(page)
        elif role == "agent":
            agent_dashboard(page)
        elif role == "secretariat":
            secretariat_dashboard(page)
        else:
            client_dashboard(page)

    def go_to_logout():
        session.clear()
        go_to_login()

    # ============================================
    # ROUTES
    # ============================================

    def route_change(e):
        route = page.route

        # Routes publiques
        if route == "/login" or route == "/":
            if session.get("user"):
                go_to_dashboard()
            else:
                login_page(page)
        elif route == "/register":
            register_page(page)
        elif route == "/mfa":
            mfa_page(page)
        elif route == "/forgot-password":
            forgot_password_page(page)

        # Routes privées
        elif route == "/dashboard":
            go_to_dashboard()
        else:
            go_to_login()

    # ============================================
    # STOCKER LES FONCTIONS
    # ============================================

    session.set("go_to_login", go_to_login)
    session.set("go_to_register", go_to_register)
    session.set("go_to_mfa", go_to_mfa)
    session.set("go_to_dashboard", go_to_dashboard)
    session.set("go_to_forgot_password", go_to_forgot_password)
    session.set("go_to_logout", go_to_logout)

    # Fermer la session proprement
    @atexit.register
    def cleanup():
        try:
            asyncio.run(close_session())
        except Exception:
            pass

    # DEMARRAGE
    page.on_route_change = route_change
    page.go("/dashboard" if session.get("user") else "/login")


if __name__ == "__main__":
    # Récupération du port dynamique attribué par Render (10000 par défaut en local/fallback)
    port = int(os.getenv("PORT", 8000))
    
    # Lancement du serveur Web Flet accessible sur le réseau
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port
    )