import flet as ft
from utils.api import (
    get_paiements_stats,
    get_paiements,
    valider_paiement,
    refuser_paiement,
)
from utils.session import session


# HEADER ADMIN (réutilisé)

def get_header_admin(page: ft.Page, active_item: str = ""):
    from pages.dashboard_admin import get_header_admin as header_admin
    return header_admin(page, active_item)


def navigate_to(page: ft.Page, destination: str):
    from pages.dashboard_admin import navigate_to as nav_to
    nav_to(page, destination)


# FONCTIONS UTILES

def show_snackbar(page: ft.Page, message: str, color):
    page.snack_bar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=color,
        duration=3000,
        open=True,
    )
    page.update()


# PAGE GESTION DES PAIEMENTS (ADMIN - SANS BOUTON DETAILS)

def gestion_paiements_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    if user.get("role") not in ['admin', 'agent', 'secretariat']:
        show_snackbar(page, "Acces reserve au personnel autorise", ft.Colors.RED)
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)
        return
    
    page.title = "Gestion des paiements"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_paiements_page(page)
    page.on_resize = on_resize
    
    # ============================================
    # STATISTIQUES
    # ============================================
    
    stats_container = ft.Container(
        content=ft.Column([
            ft.Text("Statistiques", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),
            ft.Row([], wrap=True, spacing=10),
        ]),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
    )
    
    # ============================================
    # LISTE DES PAIEMENTS
    # ============================================
    
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Liste des paiements", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),
            ft.ProgressRing(),
            ft.Text("Chargement..."),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
        expand=True,
    )
    
    # VALIDER / REFUSER UN PAIEMENT
    
    async def handle_valider_paiement(page: ft.Page, paiement_id: int):
        try:
            result = await valider_paiement(paiement_id)
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                show_snackbar(page, "Paiement valide avec succes", ft.Colors.GREEN)
                await load_paiements()
                return
        except Exception as e:
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    async def handle_refuser_paiement(page: ft.Page, paiement_id: int):
        try:
            result = await refuser_paiement(paiement_id)
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                show_snackbar(page, "Paiement refuse avec succes", ft.Colors.RED)
                await load_paiements()
                return
        except Exception as e:
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # pas dtls 
    
    def build_paiements_list(paiements):
        if not paiements:
            return ft.Column([
                ft.Text("Aucun paiement pour le moment", size=16, color=ft.Colors.GREY_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        items = []
        for p in paiements:
            if p.get("statut") == "valide":
                color = ft.Colors.GREEN
                statut_text = "Valide"
            elif p.get("statut") == "refuse":
                color = ft.Colors.RED
                statut_text = "Refuse"
            else:
                color = ft.Colors.ORANGE
                statut_text = "En attente"
            
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            # Ligne 1 : Reference + Statut
                            ft.Row([
                                ft.Text(p.get("reference_transaction", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(statut_text, size=11, color=ft.Colors.WHITE),
                                    bgcolor=color,
                                    padding=5,
                                    border_radius=10,
                                ),
                            ]),
                            # Ligne 2 : Reservation
                            ft.Text(f"Reservation: #{p.get('reservation_id', 'N/A')}"),
                            # Ligne 3 : Client
                            ft.Text(f"Client: {p.get('client_username', 'N/A')}"),
                            # Ligne 4 : Montant
                            ft.Text(f"Montant: {p.get('montant', 0):,.0f} FCFA"),
                            # Ligne 5 : Methode
                            ft.Text(f"Methode: {p.get('methode', 'N/A')}"),
                            # Ligne 6 : Date
                            ft.Text(f"Date: {p.get('date_paiement', 'N/A')[:10] if p.get('date_paiement') else 'N/A'}"),
                            # Ligne 7 : Notes (si presentes)
                            ft.Text(f"Notes: {p.get('notes', 'Aucune')}", size=12, color=ft.Colors.GREY_600) if p.get('notes') else ft.Text(""),
                            ft.Divider(height=5),
                            # Boutons d'action
                            ft.Row([
                                ft.Button(
                                    "Valider", 
                                    on_click=lambda e, pid=p['id']: page.run_task(handle_valider_paiement, page, pid),
                                    bgcolor="#4CAF50", 
                                    color="white",
                                    disabled=p.get("statut") != "en_attente",
                                ),
                                ft.Button(
                                    "Refuser", 
                                    on_click=lambda e, pid=p['id']: page.run_task(handle_refuser_paiement, page, pid),
                                    bgcolor="#F44336", 
                                    color="white",
                                    disabled=p.get("statut") != "en_attente",
                                ),
                            ], spacing=5),
                        ], spacing=5),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    )
                )
            )
        
        return ft.Row(
            items,
            wrap=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            run_spacing=15,
            height=400,
        )
    
    # ============================================
    # CHARGER LES DONNEES
    # ============================================
    
    async def load_paiements():
        try:
            paiements = await get_paiements()
            print(f"Paiements charges: {len(paiements) if paiements else 0}")
            
            # Mettre a jour les stats
            stats = await get_paiements_stats()
            stats_row = stats_container.content.controls[2]
            stats_row.controls.clear()
            
            if stats and isinstance(stats, dict):
                stat_cards = [
                    ("Total", stats.get("total_paiements", 0), ft.Colors.BLUE),
                    ("Valides", stats.get("valides", 0), ft.Colors.GREEN),
                    ("En attente", stats.get("en_attente", 0), ft.Colors.ORANGE),
                    ("Montant total", f"{stats.get('total_montant_valide', 0):,.0f} FCFA", ft.Colors.GREEN),
                ]
                for title, value, color in stat_cards:
                    stats_row.controls.append(
                        ft.Card(
                            content=ft.Container(
                                ft.Column([
                                    ft.Text(title, size=12, color=ft.Colors.GREY_600),
                                    ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=color),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                                padding=10,
                                width=150 if not is_mobile else (page.width - 40) // 2 - 10,
                            )
                        )
                    )
            
            # Mettre a jour la liste
            if paiements and isinstance(paiements, list) and len(paiements) > 0:
                list_container.content = ft.Column([
                    ft.Text("Liste des paiements", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    build_paiements_list(paiements),
                ], expand=True)
            else:
                list_container.content = ft.Column([
                    ft.Text("Liste des paiements", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.Text("Aucun paiement pour le moment", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            page.update()
            
        except Exception as e:
            print(f"Erreur paiements: {e}")
            list_container.content = ft.Text(f"Erreur: {e}", color=ft.Colors.RED)
            page.update()
    
    async def load_all():
        await load_paiements()
    
    # ============================================
    # CONSTRUIRE LA PAGE
    # ============================================
    
    page.controls.append(
        ft.Column([
            get_header_admin(page, "paiements"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des paiements", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_all), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    stats_container,
                    ft.Divider(height=20),
                    list_container,
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                expand=True,
                padding=15 if is_mobile else 20,
                bgcolor=ft.Colors.GREY_50,
            )
        ], expand=True, spacing=0)
    )
    page.update()
    
    page.run_task(load_all)