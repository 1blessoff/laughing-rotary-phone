import flet as ft
from utils.api import get_paiements_stats, get_reservations_attente, get_paiements, get_concessions, logout, put_request
from utils.session import session
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import datetime

# ============================================
# HEADER RESPONSIVE SECRETARIAT
# ============================================

def get_header_secretariat(page: ft.Page, active_item: str = ""):
    user = session.get("user", {})
    username = user.get("username", "Secretariat")
    role = "secretariat"
    
    def on_logout(e):
        page.run_task(handle_logout)
    
    async def handle_logout():
        await logout()
        session.clear()
        from pages.auth import login_page
        login_page(page)
    
    def on_edit_profile(e):
        edit_profile_page(page)
    
    is_mobile = page.width < 768
    
    menu_items = [
        ft.TextButton("Tableau de bord", on_click=lambda e: navigate_to(page, "dashboard"),
                      style=ft.ButtonStyle(color="white" if active_item!="dashboard" else "#4FC3F7")),
        ft.TextButton("Reservations", on_click=lambda e: navigate_to(page, "reservations"),
                      style=ft.ButtonStyle(color="white" if active_item!="reservations" else "#4FC3F7")),
        ft.TextButton("Paiements", on_click=lambda e: navigate_to(page, "paiements"),
                      style=ft.ButtonStyle(color="white" if active_item!="paiements" else "#4FC3F7")),
        ft.TextButton("Concessions", on_click=lambda e: navigate_to(page, "concessions"),
                      style=ft.ButtonStyle(color="white" if active_item!="concessions" else "#4FC3F7")),
        ft.TextButton("Statistiques", on_click=lambda e: navigate_to(page, "statistiques"),
                      style=ft.ButtonStyle(color="white" if active_item!="statistiques" else "#4FC3F7")),
        ft.TextButton("Profil", on_click=on_edit_profile,
                      style=ft.ButtonStyle(color="white" if active_item!="profile" else "#4FC3F7")),
    ]
    
    if not is_mobile:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Espace Secretariat", size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row(menu_items, spacing=10),
                        ft.Row([
                            ft.Text(f"{username} ({role})", size=12, color="white"),
                            ft.TextButton("Deconnexion", on_click=on_logout, style=ft.ButtonStyle(color="white")),
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
                        ft.Text("Secretariat", size=18, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row([
                            ft.Text(f"{username}", size=12, color="white"),
                            ft.PopupMenuButton(
                                icon=None,
                                content=ft.Text("Menu", color="white"),
                                items=[
                                    ft.PopupMenuItem(content=ft.Text("Tableau de bord"), on_click=lambda e: navigate_to(page, "dashboard")),
                                    ft.PopupMenuItem(content=ft.Text("Reservations"), on_click=lambda e: navigate_to(page, "reservations")),
                                    ft.PopupMenuItem(content=ft.Text("Paiements"), on_click=lambda e: navigate_to(page, "paiements")),
                                    ft.PopupMenuItem(content=ft.Text("Concessions"), on_click=lambda e: navigate_to(page, "concessions")),
                                    ft.PopupMenuItem(content=ft.Text("Statistiques"), on_click=lambda e: navigate_to(page, "statistiques")),
                                    ft.PopupMenuItem(content=ft.Text("Profil"), on_click=lambda e: edit_profile_page(page)),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(content=ft.Text("Deconnexion"), on_click=on_logout),
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


def navigate_to(page: ft.Page, destination: str):
    if destination == "dashboard":
        secretariat_dashboard(page)
    elif destination == "reservations":
        reservations_attente_page(page)
    elif destination == "paiements":
        paiements_page(page)
    elif destination == "concessions":
        concessions_page(page)
    elif destination == "statistiques":
        stats_page(page)
    elif destination == "profile":
        edit_profile_page(page)


def refresh_current_page(page: ft.Page):
    title = page.title
    if "Secretariat" in title and "Dashboard" in title:
        secretariat_dashboard(page)
    elif "Reservations" in title:
        reservations_attente_page(page)
    elif "Paiements" in title:
        paiements_page(page)
    elif "Concessions" in title:
        concessions_page(page)
    elif "Statistiques" in title:
        stats_page(page)
    elif "Profil" in title:
        edit_profile_page(page)
    else:
        secretariat_dashboard(page)


# ============================================
# MESSAGES LABEL (remplace snackbar)
# ============================================

def show_message(page: ft.Page, message: str, color=ft.Colors.GREEN):
    """Affiche un message dans un label"""
    if hasattr(page, 'message_label'):
        page.message_label.value = message
        page.message_label.color = color
        page.update()


# ============================================
# DASHBOARD SECRETARIAT
# ============================================

def secretariat_dashboard(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Secretariat Dashboard"
    page.controls.clear()
    
    username = user.get("username", "Secretariat")
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.message_label = ft.Text("", size=14, color=ft.Colors.GREEN)  # Label global
    
    main_content = ft.Column([
        ft.Row([ft.Text("Tableau de bord Secretariat", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD)]),
        ft.Text(f"Bienvenue {username}", size=18 if not is_mobile else 16),
        page.message_label,
        ft.Divider(height=20),
        ft.ProgressRing(),
        ft.Text("Chargement des statistiques..."),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True, spacing=10)
    
    page.controls.append(
        ft.Column([
            get_header_secretariat(page, "dashboard"),
            ft.Container(
                content=main_content,
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_secretariat_stats, page)


async def load_secretariat_stats(page: ft.Page):
    try:
        stats = await get_paiements_stats()
        reservations_attente = await get_reservations_attente()
        
        en_attente = reservations_attente.get("total", 0) if isinstance(reservations_attente, dict) else 0
        total_paiements = stats.get("total_paiements", 0)
        total_montant = stats.get("total_montant_valide", 0)
        en_attente_paiements = stats.get("en_attente", 0)
        
        is_mobile = page.width < 768
        
        def create_stat_card(title, value, color=ft.Colors.GREY_700, value_size=28):
            return ft.Card(
                content=ft.Container(
                    ft.Column([
                        ft.Text(title, size=14 if not is_mobile else 12, color=color, text_align=ft.TextAlign.CENTER),
                        ft.Text(str(value), size=value_size if not is_mobile else 22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=15 if is_mobile else 20,
                    width=180 if not is_mobile else page.width - 40,
                ),
                elevation=3,
            )
        
        def create_action_card(title, button_text, on_click, bgcolor="#1976D2"):
            return ft.Card(
                content=ft.Container(
                    ft.Column([
                        ft.Text(title, size=16 if not is_mobile else 14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=10),
                        ft.Button(button_text, on_click=on_click, bgcolor=bgcolor, color="white", width=160 if not is_mobile else page.width - 60),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, tight=True),
                    padding=15,
                    width=190 if not is_mobile else page.width - 20,
                ),
                elevation=3,
            )
        
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "dashboard"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Tableau de bord Secretariat", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=20),
                        
                        ft.Text("Statistiques", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_stat_card("Reservations attente", en_attente, ft.Colors.ORANGE),
                            create_stat_card("Paiements total", total_paiements, ft.Colors.BLUE),
                            create_stat_card("Paiements en attente", en_attente_paiements, ft.Colors.ORANGE),
                            create_stat_card("Montant total", f"{total_montant:,.0f} FCFA", ft.Colors.GREEN, 20),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20),
                        
                        ft.Text("Actions rapides", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_action_card("Reservations", "Gerer", lambda e: navigate_to(page, "reservations"), "#11695D"),
                            create_action_card("Paiements", "Gerer", lambda e: navigate_to(page, "paiements"), "#FF6F00"),
                            create_action_card("Concessions", "Voir", lambda e: navigate_to(page, "concessions"), "#9C27B0"),
                            create_action_card("Statistiques", "Voir", lambda e: navigate_to(page, "statistiques"), "#1976D2"),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=15),
                    expand=True,
                    padding=15 if is_mobile else 20,
                )
            ], expand=True, spacing=0)
        )
        page.update()
        
    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "dashboard"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Erreur de chargement", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(str(e), size=14),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_secretariat_stats, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    expand=True,
                    padding=20,
                )
            ], expand=True, spacing=0)
        )
        page.update()


# ============================================
# RESERVATIONS EN ATTENTE
# ============================================

def reservations_attente_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Reservations en attente"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.message_label = ft.Text("", size=14, color=ft.Colors.GREEN)
    
    page.controls.append(
        ft.Column([
            get_header_secretariat(page, "reservations"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_reservations_attente_list, page), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    page.message_label,
                    ft.ProgressRing(),
                    ft.Text("Chargement..."),
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_reservations_attente_list, page)


async def load_reservations_attente_list(page: ft.Page):
    try:
        data = await get_reservations_attente()
        reservations = data.get("reservations", []) if isinstance(data, dict) else []
        is_mobile = page.width < 768

        if not reservations:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_secretariat(page, "reservations"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_reservations_attente_list, page), bgcolor="#1976D2", color="white"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            page.message_label,
                            ft.Text("Aucune reservation en attente", size=16, color=ft.Colors.GREY_600),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    ),
                ], expand=True, spacing=0)
            )
            page.update()
            return

        items = []
        for r in reservations:
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(f"Reservation #{r.get('id', 'N/A')}", weight=ft.FontWeight.BOLD, size=16),
                                ft.Container(ft.Text("En attente", size=12, color="white"), bgcolor=ft.Colors.ORANGE, padding=5, border_radius=5),
                            ]),
                            ft.Text(f"Defunt: {r.get('nom_defunt', 'N/A')}", size=14),
                            ft.Text(f"Caveau: {r.get('caveau_reference', 'N/A')}", size=14),
                            ft.Text(f"Client: {r.get('client_username', 'N/A')}", size=14),
                            ft.Row([
                                ft.Button("Valider", on_click=lambda e, rid=r.get('id'): page.run_task(valider_reservation_action, page, rid),
                                          bgcolor=ft.Colors.GREEN, color="white", expand=is_mobile),
                                ft.Button("Refuser", on_click=lambda e, rid=r.get('id'): page.run_task(refuser_reservation_action, page, rid),
                                          bgcolor=ft.Colors.RED, color="white", expand=is_mobile),
                            ], spacing=10),
                        ], spacing=5),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    ),
                    elevation=2,
                )
            )

        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_reservations_attente_list, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        page.message_label,
                        ft.Row(items, wrap=True, scroll=ft.ScrollMode.AUTO, spacing=15, run_spacing=15, height=500),
                    ], expand=True),
                    expand=True,
                    padding=15 if is_mobile else 20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()
    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_reservations_attente_list, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


async def valider_reservation_action(page: ft.Page, reservation_id: int):
    from utils.api import valider_reservation
    try:
        result = await valider_reservation(reservation_id)
        if not result or "error" in result:
            erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
            show_message(page, f"Erreur: {erreur}", ft.Colors.RED)
            return
        show_message(page, f"Reservation #{reservation_id} validee", ft.Colors.GREEN)
        await load_reservations_attente_list(page)
    except Exception as e:
        show_message(page, f"Erreur: {e}", ft.Colors.RED)


async def refuser_reservation_action(page: ft.Page, reservation_id: int):
    from utils.api import refuser_reservation
    try:
        result = await refuser_reservation(reservation_id, "Refuse par le secretariat")
        if not result or "error" in result:
            erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
            show_message(page, f"Erreur: {erreur}", ft.Colors.RED)
            return
        show_message(page, f"Reservation #{reservation_id} refusee", ft.Colors.RED)
        await load_reservations_attente_list(page)
    except Exception as e:
        show_message(page, f"Erreur: {e}", ft.Colors.RED)


# ============================================
# PAIEMENTS
# ============================================

def paiements_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Paiements"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.message_label = ft.Text("", size=14, color=ft.Colors.GREEN)
    
    page.controls.append(
        ft.Column([
            get_header_secretariat(page, "paiements"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des paiements", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_paiements_list, page), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    page.message_label,
                    ft.ProgressRing(),
                    ft.Text("Chargement..."),
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_paiements_list, page)


async def load_paiements_list(page: ft.Page):
    try:
        paiements = await get_paiements()
        is_mobile = page.width < 768

        if not paiements or (isinstance(paiements, dict) and "error" in paiements):
            paiements = []

        paiements = sorted(paiements, key=lambda p: 0 if p.get("statut") == "en_attente" else 1)

        items = []
        for p in paiements:
            statut = p.get("statut", "inconnu")
            couleur = {
                "en_attente": ft.Colors.ORANGE,
                "valide": ft.Colors.GREEN,
                "refuse": ft.Colors.RED,
                "echoue": ft.Colors.RED,
            }.get(statut, ft.Colors.GREY)

            actions = []
            if statut == "en_attente":
                actions = [
                    ft.Button("Valider", on_click=lambda e, pid=p['id']: page.run_task(valider_paiement_action, page, pid), bgcolor=ft.Colors.GREEN, color="white", expand=is_mobile),
                    ft.Button("Refuser", on_click=lambda e, pid=p['id']: page.run_task(refuser_paiement_action, page, pid), bgcolor=ft.Colors.RED, color="white", expand=is_mobile),
                ]

            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(p.get("reference_transaction", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(ft.Text(statut, size=11, color="white"), bgcolor=couleur, padding=5, border_radius=5),
                            ]),
                            ft.Text(f"Montant: {p.get('montant', 0):,.0f} FCFA"),
                            ft.Text(f"Date: {p.get('date_paiement', 'N/A')[:10] if p.get('date_paiement') else 'N/A'}"),
                            ft.Row(actions, spacing=10) if actions else ft.Container(),
                        ], spacing=5),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    ),
                    elevation=2,
                )
            )

        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "paiements"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Gestion des paiements", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_paiements_list, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        page.message_label,
                        ft.Row(items, wrap=True, scroll=ft.ScrollMode.AUTO, spacing=15, run_spacing=15, height=500) if items else ft.Text("Aucun paiement", size=16, color=ft.Colors.GREY_600),
                    ], expand=True),
                    expand=True,
                    padding=15 if is_mobile else 20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()
    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "paiements"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_paiements_list, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


async def valider_paiement_action(page: ft.Page, paiement_id: int):
    from utils.api import valider_paiement
    try:
        result = await valider_paiement(paiement_id)
        if not result or "error" in result:
            erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
            show_message(page, f"Erreur: {erreur}", ft.Colors.RED)
            return
        show_message(page, "Paiement valide, facture envoyee", ft.Colors.GREEN)
        await load_paiements_list(page)
    except Exception as e:
        show_message(page, f"Erreur: {e}", ft.Colors.RED)


async def refuser_paiement_action(page: ft.Page, paiement_id: int):
    from utils.api import refuser_paiement
    try:
        result = await refuser_paiement(paiement_id)
        if not result or "error" in result:
            erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
            show_message(page, f"Erreur: {erreur}", ft.Colors.RED)
            return
        show_message(page, "Paiement refuse", ft.Colors.RED)
        await load_paiements_list(page)
    except Exception as e:
        show_message(page, f"Erreur: {e}", ft.Colors.RED)


# ============================================
# CONCESSIONS
# ============================================

def concessions_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Concessions"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.message_label = ft.Text("", size=14, color=ft.Colors.GREEN)
    
    page.controls.append(
        ft.Column([
            get_header_secretariat(page, "concessions"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_concessions_list, page), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    page.message_label,
                    ft.ProgressRing(),
                    ft.Text("Chargement..."),
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_concessions_list, page)


async def load_concessions_list(page: ft.Page):
    try:
        concessions = await get_concessions()
        is_mobile = page.width < 768

        if not concessions or (isinstance(concessions, dict) and "error" in concessions):
            concessions = []

        items = []
        for c in concessions:
            expiree = c.get("est_expiree", False)
            couleur = ft.Colors.RED if expiree else ft.Colors.GREEN
            statut_txt = "Expiree" if expiree else "Active"
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c.get("numero_contrat", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(ft.Text(statut_txt, size=11, color="white"), bgcolor=couleur, padding=5, border_radius=5),
                            ]),
                            ft.Text(f"Type: {c.get('type_concession', 'N/A')}"),
                            ft.Text(f"Debut: {c.get('date_debut', 'N/A')}"),
                            ft.Text(f"Fin: {c.get('date_fin') or 'Perpetuelle'}"),
                        ], spacing=5),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    ),
                    elevation=2,
                )
            )

        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "concessions"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Gestion des concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_concessions_list, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        page.message_label,
                        ft.Row(items, wrap=True, scroll=ft.ScrollMode.AUTO, spacing=15, run_spacing=15, height=500) if items else ft.Text("Aucune concession", size=16, color=ft.Colors.GREY_600),
                    ], expand=True),
                    expand=True,
                    padding=15 if is_mobile else 20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()
    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "concessions"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_concessions_list, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


# ============================================
# STATISTIQUES AVEC EXPORT PDF
# ============================================

def stats_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Statistiques"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.message_label = ft.Text("", size=14, color=ft.Colors.GREEN)
    
    page.controls.append(
        ft.Column([
            get_header_secretariat(page, "statistiques"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Statistiques", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_stats_detail, page), bgcolor="#1976D2", color="white"),
                        ft.Button("Exporter PDF", on_click=lambda e: page.run_task(exporter_stats_pdf, page), bgcolor="#4CAF50", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    page.message_label,
                    ft.ProgressRing(),
                    ft.Text("Chargement..."),
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_stats_detail, page)


async def exporter_stats_pdf(page: ft.Page):
    """Exporter les statistiques en PDF"""
    try:
        stats = await get_paiements_stats()
        
        if not stats or "error" in stats:
            show_message(page, "Aucune donnee a exporter", ft.Colors.RED)
            return
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Titre
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=20)
        story.append(Paragraph("Rapport des statistiques - Gestion Funeraire", title_style))
        story.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Paragraph(" ", styles['Normal']))
        
        # Donnees generales
        data = [
            ["Indicateur", "Valeur"],
            ["Total paiements", str(stats.get("total_paiements", 0))],
            ["Paiements valides", str(stats.get("valides", 0))],
            ["Paiements en attente", str(stats.get("en_attente", 0))],
            ["Paiements refuses", str(stats.get("refuses", 0))],
            ["Montant total valide", f"{stats.get('total_montant_valide', 0):,.0f} FCFA"],
            ["Montant total attente", f"{stats.get('total_montant_attente', 0):,.0f} FCFA"],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        
        # Methode de paiement
        par_methode = stats.get("par_methode", {})
        if par_methode:
            story.append(Paragraph(" ", styles['Normal']))
            story.append(Paragraph("Repartition par methode", styles['Heading3']))
            
            methode_data = [["Methode", "Nombre"]]
            for methode, nombre in par_methode.items():
                methode_data.append([methode, str(nombre)])
            
            methode_table = Table(methode_data, colWidths=[2.5*inch, 2.5*inch])
            methode_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(methode_table)
        
        doc.build(story)
        buffer.seek(0)
        
        # Sauvegarder le PDF
        pdf_path = f"statistiques_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(buffer.getvalue())
        
        show_message(page, f"PDF exporte: {pdf_path}", ft.Colors.GREEN)
        
        # Ouvrir le PDF
        import os
        import webbrowser
        webbrowser.open(os.path.abspath(pdf_path))
        
    except Exception as e:
        show_message(page, f"Erreur export: {e}", ft.Colors.RED)


async def load_stats_detail(page: ft.Page):
    try:
        stats = await get_paiements_stats()
        reservations_attente = await get_reservations_attente()
        is_mobile = page.width < 768

        if not stats or "error" in stats:
            stats = {}

        par_methode = stats.get("par_methode", {}) or {}
        total_paiements_par_methode = sum(par_methode.values()) if par_methode else 0

        def carte(titre, valeur, couleur=ft.Colors.GREY_700):
            return ft.Container(
                content=ft.Column([
                    ft.Text(titre, size=13, color=couleur, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(valeur), size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.GREY_300),
                width=180 if not is_mobile else page.width - 40,
            )

        cartes_generales = ft.Row([
            carte("Paiements valides", stats.get("valides", 0), ft.Colors.GREEN),
            carte("Paiements en attente", stats.get("en_attente", 0), ft.Colors.ORANGE),
            carte("Paiements refuses/echoues", stats.get("refuses", 0) + stats.get("echoues", 0), ft.Colors.RED),
            carte("Reservations en attente", reservations_attente.get("total", 0) if isinstance(reservations_attente, dict) else 0, ft.Colors.ORANGE),
        ], wrap=True, spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        cartes_montants = ft.Row([
            carte("Montant valide", f"{stats.get('total_montant_valide', 0):,.0f} FCFA", ft.Colors.GREEN),
            carte("Montant en attente", f"{stats.get('total_montant_attente', 0):,.0f} FCFA", ft.Colors.ORANGE),
        ], wrap=True, spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        # ✅ Repartition par methode (nombre seulement, pas FCFA)
        lignes_methodes = []
        if par_methode:
            for methode, nombre in par_methode.items():
                lignes_methodes.append(
                    ft.Row([
                        ft.Text(methode, size=14, expand=True),
                        ft.Text(str(nombre), size=14, weight=ft.FontWeight.BOLD),
                    ])
                )
        else:
            lignes_methodes.append(ft.Text("Aucune donnee", color=ft.Colors.GREY_600))

        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "statistiques"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Statistiques", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Exporter PDF", on_click=lambda e: page.run_task(exporter_stats_pdf, page), bgcolor="#4CAF50", color="white"),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_stats_detail, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=15),
                        cartes_generales,
                        ft.Divider(height=15),
                        cartes_montants,
                        ft.Divider(height=20),
                        ft.Text("Repartition par methode de paiement", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Column(lignes_methodes, spacing=8) if lignes_methodes else ft.Text("Aucune donnee", color=ft.Colors.GREY_600),
                            padding=15,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=8,
                            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.Colors.GREY_300),
                        ),
                    ], scroll=ft.ScrollMode.AUTO, expand=True),
                    expand=True,
                    padding=15 if is_mobile else 20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()
    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_secretariat(page, "statistiques"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_stats_detail, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


# ============================================
# PROFIL
# ============================================

def edit_profile_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Profil"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    user = session.get("user", {})
    username = user.get("username", "")
    email = user.get("email", "")
    phone = user.get("phone", "")

    message_label = ft.Text("", size=14, color=ft.Colors.GREEN)

    def save_profile(e):
        data = {
            "username": username_field.value,
            "phone": phone_field.value,
        }
        if password_field.value:
            data["password"] = password_field.value
        
        print(f"📤 Donnees envoyees: {data}")
        page.run_task(handle_update_profile, page, data)

    async def handle_update_profile(page: ft.Page, data: dict):
        try:
            print(f"📤 handle_update_profile: {data}")
            result = await put_request("auth/update-profile", data)
            print(f"📥 Reponse: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message_label.value = f"Erreur: {result['error']}"
                    message_label.color = ft.Colors.RED
                    page.update()
                    return
                if result.get("success"):
                    user = session.get("user", {})
                    user["username"] = data.get("username", user.get("username"))
                    user["phone"] = data.get("phone", user.get("phone"))
                    session.set("user", user)
                    message_label.value = "Profil mis a jour avec succes"
                    message_label.color = ft.Colors.GREEN
                    page.update()
                    return
            
            message_label.value = "Erreur lors de la mise a jour"
            message_label.color = ft.Colors.RED
            page.update()
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            message_label.value = f"Erreur: {e}"
            message_label.color = ft.Colors.RED
            page.update()

    username_field = ft.TextField(
        label="Nom d'utilisateur",
        value=username,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.WHITE,
        border_color="#1A237E",
        focused_border_color="#1976D2",
    )
    email_field = ft.TextField(
        label="Email",
        value=email,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.GREY_200,
        read_only=True,
        disabled=True,
    )
    phone_field = ft.TextField(
        label="Telephone",
        value=phone,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.WHITE,
        border_color="#1A237E",
        focused_border_color="#1976D2",
    )
    password_field = ft.TextField(
        label="Nouveau mot de passe",
        password=True,
        can_reveal_password=True,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.WHITE,
        border_color="#1A237E",
        focused_border_color="#1976D2",
        hint_text="Laissez vide pour ne pas changer",
    )

    form = ft.Container(
        content=ft.Column([
            ft.Text("Informations personnelles", size=18, weight=ft.FontWeight.BOLD, color="#1A237E"),
            ft.Divider(height=10),
            username_field,
            email_field,
            phone_field,
            ft.Divider(height=15),
            ft.Text("Securite", size=18, weight=ft.FontWeight.BOLD, color="#1A237E"),
            ft.Divider(height=10),
            password_field,
            ft.Divider(height=15),
            message_label,
            ft.Row([
                ft.Button("Enregistrer", on_click=save_profile, bgcolor="#1976D2", color="white"),
                ft.Button("Retour", on_click=lambda e: secretariat_dashboard(page), bgcolor=ft.Colors.GREY_400, color="white"),
            ], spacing=10),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        padding=25,
        bgcolor="#F5F7FA",
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
    )

    page.controls.append(
        ft.Column([
            get_header_secretariat(page, "profile"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Mon profil", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=20),
                    form,
                ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
                bgcolor=ft.Colors.GREY_50,
            ),
        ], expand=True, spacing=0)
    )
    page.update()


def login_page(page: ft.Page):
    from pages.auth import login_page as auth_login
    auth_login(page)