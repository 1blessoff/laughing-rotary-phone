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
        render_route()

    def go_to_register():
        page.route = "/register"
        render_route()

    def go_to_mfa():
        page.route = "/mfa"
        render_route()

    def go_to_forgot_password():
        page.route = "/forgot-password"
        render_route()

    def go_to_dashboard():
        page.route = "/dashboard"
        user = session.get("user")
        if not user:
            go_to_login()
            return
        
        # Vider la page avant d'afficher le dashboard
        page.controls.clear()
        role = user.get("role", "client")
        if role == "admin":
            admin_dashboard(page)
        elif role == "agent":
            agent_dashboard(page)
        elif role == "secretariat":
            secretariat_dashboard(page)
        else:
            client_dashboard(page)
        page.update()

    def go_to_logout():
        session.clear()
        go_to_login()

    # ============================================
    # RENDU DE ROUTE (Régle la page blanche)
    # ============================================
    def render_route():
        page.controls.clear()  # Vider les anciens éléments graphiques
        route = page.route

        if route in ["/login", "/"]:
            if session.get("user"):
                go_to_dashboard()
                return
            login_page(page)
        elif route == "/register":
            register_page(page)
        elif route == "/mfa":
            mfa_page(page)
        elif route == "/forgot-password":
            forgot_password_page(page)
        elif route == "/dashboard":
            go_to_dashboard()
            return
        else:
            login_page(page)

        page.update()  # Forcer la mise à jour visuelle du navigateur

    def route_change(e):
        render_route()

    # ============================================
    # STOCKER LES FONCTIONS DANS LA SESSION
    # ============================================
    session.set("go_to_login", go_to_login)
    session.set("go_to_register", go_to_register)
    session.set("go_to_mfa", go_to_mfa)
    session.set("go_to_dashboard", go_to_dashboard)
    session.set("go_to_forgot_password", go_to_forgot_password)
    session.set("go_to_logout", go_to_logout)

    # Nettoyage à la fermeture
    @atexit.register
    def cleanup():
        try:
            asyncio.run(close_session())
        except Exception:
            pass

    # INITIALISATION
    page.on_route_change = route_change
    
    # Route initiale
    initial_route = "/dashboard" if session.get("user") else "/login"
    page.route = initial_route
    render_route()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port
    )