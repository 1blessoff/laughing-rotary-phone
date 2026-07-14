import flet as ft
from utils.api import (
    get_exhumations,
    create_exhumation,
    approuver_exhumation,
    refuser_exhumation,
    realiser_exhumation,
    get_concessions,
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


# PAGE GESTION DES EXHUMATIONS

def gestion_exhumations_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    if user.get("role") not in ['admin', 'agent', 'secretariat']:
        show_snackbar(page, "Accès réservé au personnel autorisé", ft.Colors.RED)
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)
        return
    
    page.title = "Gestion des exhumations"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_exhumations_page(page)
    page.on_resize = on_resize
    
    # ============================================
    # FORMULAIRE DE DEMANDE
    # ============================================
    
    concession_dropdown = ft.Dropdown(
        label="Concession",
        width=400 if not is_mobile else page.width - 40,
        options=[],
        value=None,
    )
    
    motif_field = ft.TextField(
        label="Motif de l'exhumation",
        width=400 if not is_mobile else page.width - 40,
        hint_text="Ex: Réhabilitation du site, transfert, etc.",
        multiline=True,
        min_lines=3,
        max_lines=5,
    )
    
    notes_field = ft.TextField(
        label="Notes (optionnel)",
        width=400 if not is_mobile else page.width - 40,
        multiline=True,
        min_lines=2,
        max_lines=4,
    )
    
    message = ft.Text("", color=ft.Colors.RED)
    
    def on_create(e):
        if not concession_dropdown.value:
            show_snackbar(page, "Veuillez sélectionner une concession", ft.Colors.RED)
            return
        
        if not motif_field.value:
            show_snackbar(page, "Veuillez saisir un motif", ft.Colors.RED)
            return
        
        data = {
            "concession_id": int(concession_dropdown.value),
            "motif": motif_field.value,
            "notes": notes_field.value or "",
        }
        page.run_task(handle_create_exhumation, page, data)
    
    async def handle_create_exhumation(page: ft.Page, data: dict):
        try:
            result = await create_exhumation(data)
            print(f"Résultat exhumation: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                if "id" in result:
                    show_snackbar(page, f"Demande d'exhumation créée (ID: {result.get('id')})", ft.Colors.GREEN)
                    motif_field.value = ""
                    notes_field.value = ""
                    await load_exhumations()
                    await load_concessions()
                    return
            
            show_snackbar(page, "Erreur lors de la création", ft.Colors.RED)
            
        except Exception as e:
            print(f"Erreur: {e}")
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # ============================================
    # ACTIONS SUR LES EXHUMATIONS
    # ============================================
    
    async def handle_approuver(page: ft.Page, exhumation_id: int):
        try:
            result = await approuver_exhumation(exhumation_id)
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                show_snackbar(page, "Exhumation approuvée", ft.Colors.GREEN)
                await load_exhumations()
                return
        except Exception as e:
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    async def handle_refuser(page: ft.Page, exhumation_id: int):
        try:
            result = await refuser_exhumation(exhumation_id, "Refusée par l'administrateur")
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                show_snackbar(page, "Exhumation refusée", ft.Colors.RED)
                await load_exhumations()
                return
        except Exception as e:
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    async def handle_realiser(page: ft.Page, exhumation_id: int):
        try:
            result = await realiser_exhumation(exhumation_id)
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                show_snackbar(page, "Exhumation réalisée", ft.Colors.GREEN)
                await load_exhumations()
                return
        except Exception as e:
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # ============================================
    # LISTE DES EXHUMATIONS
    # ============================================
    
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Liste des exhumations", size=18, weight=ft.FontWeight.BOLD),
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
    
    async def load_concessions():
        try:
            concessions = await get_concessions()
            options = []
            for c in concessions:
                options.append(
                    ft.dropdown.Option(
                        str(c["id"]), 
                        f"{c.get('numero_contrat', 'N/A')} - #{c.get('reservation_id', 'N/A')}"
                    )
                )
            concession_dropdown.options = options
            if options:
                concession_dropdown.value = options[0].key
            page.update()
        except Exception as e:
            print(f"Erreur chargement concessions: {e}")
    
    def build_exhumations_list(exhumations):
        if not exhumations:
            return ft.Column([
                ft.Text("Aucune exhumation", size=16, color=ft.Colors.GREY_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        items = []
        for e in exhumations:
            statut = e.get("statut", "demande")
            
            if statut == "demande":
                color = ft.Colors.ORANGE
                label = "En attente"
            elif statut == "approuvee":
                color = ft.Colors.GREEN
                label = "Approuvée"
            elif statut == "realisee":
                color = ft.Colors.BLUE
                label = "Réalisée"
            else:
                color = ft.Colors.RED
                label = "Refusée"
            
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(f"Exhumation #{e.get('id', 'N/A')}", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(label, size=11, color=ft.Colors.WHITE),
                                    bgcolor=color,
                                    padding=5,
                                    border_radius=10,
                                ),
                            ]),
                            ft.Text(f"Concession: {e.get('concession_numero', 'N/A')}"),
                            ft.Text(f"Motif: {e.get('motif', 'N/A')}"),
                            ft.Text(f"Date demande: {e.get('date_demande', 'N/A')[:10] if e.get('date_demande') else 'N/A'}"),
                            ft.Row([
                                ft.Button(
                                    " Approuver",
                                    on_click=lambda e, eid=e['id']: page.run_task(handle_approuver, page, eid),
                                    bgcolor="#4CAF50", color="white",
                                    disabled=statut != "demande",
                                ),
                                ft.Button(
                                    " Refuser",
                                    on_click=lambda e, eid=e['id']: page.run_task(handle_refuser, page, eid),
                                    bgcolor="#F44336", color="white",
                                    disabled=statut != "demande",
                                ),
                                ft.Button(
                                    " Réaliser",
                                    on_click=lambda e, eid=e['id']: page.run_task(handle_realiser, page, eid),
                                    bgcolor="#2196F3", color="white",
                                    disabled=statut != "approuvee",
                                ),
                            ], spacing=5),
                        ]),
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
    
    async def load_exhumations():
        try:
            exhumations = await get_exhumations()
            print(f"Exhumations chargées: {len(exhumations) if exhumations else 0}")
            
            if exhumations and isinstance(exhumations, list) and len(exhumations) > 0:
                list_container.content = ft.Column([
                    ft.Text("Liste des exhumations", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    build_exhumations_list(exhumations),
                ], expand=True)
            else:
                list_container.content = ft.Column([
                    ft.Text("Liste des exhumations", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.Text(" Aucune exhumation", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            page.update()
            
        except Exception as e:
            print(f"Erreur exhumations: {e}")
            list_container.content = ft.Text(f"Erreur: {e}", color=ft.Colors.RED)
            page.update()
    
    async def load_all():
        await load_concessions()
        await load_exhumations()
    
    # ============================================
    # FORMULAIRE
    # ============================================
    
    formulaire = ft.Container(
        content=ft.Column([
            ft.Text(" Nouvelle demande d'exhumation", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
            ft.Divider(height=10),
            concession_dropdown,
            motif_field,
            notes_field,
            ft.Row([
                ft.Button("Réinitialiser", on_click=lambda e: motif_field.value, bgcolor=ft.Colors.GREY_400, color="white", expand=is_mobile),
                ft.Button("Créer la demande", on_click=on_create, bgcolor="#4CAF50", color="white", expand=is_mobile),
            ], spacing=10),
            message,
        ], spacing=10),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
    )
    
    # ============================================
    # CONSTRUIRE LA PAGE
    # ============================================
    
    page.controls.append(
        ft.Column([
            get_header_admin(page, "exhumations"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des exhumations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button(" Rafraîchir", on_click=lambda e: page.run_task(load_all), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    formulaire,
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