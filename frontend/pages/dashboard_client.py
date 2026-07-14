import flet as ft
from utils.session import session

# ============================================
# HEADER RESPONSIVE CLIENT
# ============================================

def get_header_client(page: ft.Page, active_item: str = ""):
    from utils.api import logout

    user = session.get("user", {})
    username = user.get("username", "Client")
    role = "client"

    def on_logout(e):
        page.run_task(handle_logout)

    async def handle_logout():
        await logout()
        session.clear()
        from pages.auth import login_page
        login_page(page)

    def on_edit_profile(e):
        from pages.profile_client import edit_profile_page
        edit_profile_page(page)

    is_mobile = page.width < 768

    menu_items = [
        ft.TextButton("Tableau de bord", on_click=lambda e: navigate_to(page, "dashboard"),
                      style=ft.ButtonStyle(color="white" if active_item != "dashboard" else "#4FC3F7")),
        ft.TextButton("Carte", on_click=lambda e: navigate_to(page, "carte"),
                      style=ft.ButtonStyle(color="white" if active_item != "carte" else "#4FC3F7")),
        ft.TextButton("Mes réservations", on_click=lambda e: navigate_to(page, "reservations"),
                      style=ft.ButtonStyle(color="white" if active_item != "reservations" else "#4FC3F7")),
        ft.TextButton("Mes paiements", on_click=lambda e: navigate_to(page, "paiements"),
                      style=ft.ButtonStyle(color="white" if active_item != "paiements" else "#4FC3F7")),
        ft.TextButton("Mes concessions", on_click=lambda e: navigate_to(page, "concessions"),
                      style=ft.ButtonStyle(color="white" if active_item != "concessions" else "#4FC3F7")),
        ft.TextButton("Mon profil", on_click=on_edit_profile,
                      style=ft.ButtonStyle(color="white" if active_item != "profile" else "#4FC3F7")),
    ]

    if not is_mobile:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Espace Client", size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row(menu_items, spacing=10),
                        ft.Row([
                            ft.Text(f"{username} ({role})", size=12, color="white"),
                            ft.TextButton("Déconnexion", on_click=on_logout, style=ft.ButtonStyle(color="white")),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#1976D2",
                ),
            ], spacing=0),
            width=page.width,
        )
    else:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Client", size=18, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row([
                            ft.Text(f"{username}", size=12, color="white"),
                            ft.PopupMenuButton(
                                icon=None,
                                content=ft.Text("Menu", color="white"),
                                items=[
                                    ft.PopupMenuItem(content=ft.Text("Tableau de bord"), on_click=lambda e: navigate_to(page, "dashboard")),
                                    ft.PopupMenuItem(content=ft.Text("Carte"), on_click=lambda e: navigate_to(page, "carte")),
                                    ft.PopupMenuItem(content=ft.Text("Mes réservations"), on_click=lambda e: navigate_to(page, "reservations")),
                                    ft.PopupMenuItem(content=ft.Text("Mes paiements"), on_click=lambda e: navigate_to(page, "paiements")),
                                    ft.PopupMenuItem(content=ft.Text("Mes concessions"), on_click=lambda e: navigate_to(page, "concessions")),
                                    ft.PopupMenuItem(content=ft.Text("Mon profil"), on_click=on_edit_profile),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(content=ft.Text("Déconnexion"), on_click=on_logout),
                                ],
                            ),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#1976D2",
                ),
            ], spacing=0),
            width=page.width,
        )


# ============================================
# NAVIGATION
# ============================================
# FIX : chaque destination pointe maintenant vers son propre fichier.
# "paiements" pointait auparavant vers un doublon interne en lecture seule
# qui ne contenait pas le formulaire de création de paiement.

def navigate_to(page: ft.Page, destination: str):
    if destination == "dashboard":
        client_dashboard(page)
    elif destination == "carte":
        from pages.carte_client import carte_client_page
        carte_client_page(page)
    elif destination == "caveaux":
        from pages.caveaux_client import caveaux_disponibles_page
        caveaux_disponibles_page(page)
    elif destination == "reservations":
        from pages.reservations_client import mes_reservations_page
        mes_reservations_page(page)
    elif destination == "paiements":
        from pages.gestion_paiements_client import gestion_paiements_client_page
        gestion_paiements_client_page(page)
    elif destination == "concessions":
        from pages.concessions_client import mes_concessions_page
        mes_concessions_page(page)
    elif destination == "profile":
        from pages.profile_client import edit_profile_page
        edit_profile_page(page)
    elif destination == "create_reservation":
        from pages.reservations_client import create_reservation_page
        create_reservation_page(page)


def refresh_current_page(page: ft.Page):
    title = page.title
    if "Client Dashboard" in title:
        client_dashboard(page)
    elif "Carte" in title:
        from pages.carte_client import carte_client_page
        carte_client_page(page)
    elif "Caveaux" in title:
        from pages.caveaux_client import caveaux_disponibles_page
        caveaux_disponibles_page(page)
    elif "réservation" in title.lower():
        from pages.reservations_client import mes_reservations_page
        mes_reservations_page(page)
    elif "Mes paiements" in title:
        from pages.gestion_paiements_client import gestion_paiements_client_page
        gestion_paiements_client_page(page)
    elif "Mes concessions" in title:
        from pages.concessions_client import mes_concessions_page
        mes_concessions_page(page)
    elif "Mon profil" in title:
        from pages.profile_client import edit_profile_page
        edit_profile_page(page)
    else:
        client_dashboard(page)


# ============================================
# DASHBOARD CLIENT
# ============================================

def client_dashboard(page: ft.Page):
    # Garde de session : si l'utilisateur n'est plus authentifié
    # (session expirée / vidée), on le renvoie au login au lieu
    # d'afficher un tableau de bord "fantôme".
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Client Dashboard"
    page.controls.clear()

    username = user.get("username", "Client")
    is_mobile = page.width < 768

    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    card_width = 220
    card_height = 180
    btn_width = card_width - 40
    if is_mobile:
        card_width = page.width - 40
        card_height = 160
        btn_width = card_width - 30

    def create_action_card(title, button_text, on_click):
        return ft.Card(
            content=ft.Container(
                ft.Column([
                    ft.Text(title, size=16 if not is_mobile else 14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=10),
                    ft.Button(button_text, on_click=on_click, bgcolor="#1976D2", color="white", width=btn_width),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, tight=True),
                padding=15,
                width=card_width,
                height=card_height,
            ),
            elevation=3,
        )

    if not is_mobile:
        action_cards = ft.Row(
            controls=[
                create_action_card("Carte des caveaux", "Voir la carte", lambda e: navigate_to(page, "carte")),
                create_action_card("Caveaux disponibles", "Voir les caveaux", lambda e: navigate_to(page, "caveaux")),
                create_action_card("Nouvelle réservation", "Réserver", lambda e: navigate_to(page, "create_reservation")),
                create_action_card("Mes paiements", "Voir mes paiements", lambda e: navigate_to(page, "paiements")),
                create_action_card("Mes concessions", "Voir mes concessions", lambda e: navigate_to(page, "concessions")),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True,
        )
    else:
        action_cards = ft.Column(
            controls=[
                create_action_card("Caveaux disponibles", "Voir", lambda e: navigate_to(page, "caveaux")),
                create_action_card("Nouvelle réservation", "Réserver", lambda e: navigate_to(page, "create_reservation")),
                create_action_card("Mes paiements", "Voir", lambda e: navigate_to(page, "paiements")),
                create_action_card("Mes concessions", "Voir", lambda e: navigate_to(page, "concessions")),
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    main_content = ft.Column([
        ft.Row([ft.Text("Tableau de bord Client", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD)]),
        ft.Text(f"Bienvenue {username}", size=18 if not is_mobile else 16),
        ft.Divider(height=20),
        action_cards,
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

    page.controls.append(
        ft.Column([
            get_header_client(page, "dashboard"),
            ft.Container(
                content=main_content,
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()


# ============================================
# FONCTIONS UTILES PARTAGEES
# ============================================

def show_snackbar(page: ft.Page, message: str, color):
    page.snack_bar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=color,
        duration=3000,
        open=True,
    )
    page.update()


def login_page(page: ft.Page):
    from pages.auth import login_page as auth_login
    auth_login(page)