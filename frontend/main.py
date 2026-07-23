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
    
    # Configuration Responsive
    page.padding = 0
    page.spacing = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START

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
    # RENDU DE ROUTE (CORRECTION MAX_WIDTH & ALIGNMENT)
    # ============================================
    def render_route():
        page.controls.clear()
        route = page.route

        # Déterminer la page à charger
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

        # Encapsulation Responsive
        if route != "/dashboard" and len(page.controls) > 0:
            content_controls = list(page.controls)
            page.controls.clear()
            
            responsive_wrapper = ft.Container(
                content=ft.Column(
                    controls=content_controls,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
                padding=20,
                width=500,  # <--- FIX: Utilisation de 'width' au lieu de 'max_width'
                expand=True,
            )
            
            page.add(
                ft.Container(
                    content=responsive_wrapper,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            )

        page.update()

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
    
    initial_route = "/dashboard" if session.get("user") else "/login"
    page.route = initial_route
    render_route()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # FIX: Utilisation de ft.run() à la place de ft.app() pour Flet 0.80+
    ft.run(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port
    )