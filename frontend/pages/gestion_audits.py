import flet as ft
from utils.api import get_request
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


# PAGE GESTION DES AUDITS

def gestion_audits_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    if user.get("role") != "admin":
        show_snackbar(page, "Accès réservé aux administrateurs", ft.Colors.RED)
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)
        return
    
    page.title = "Audit Logs"
    page.controls.clear()
    is_mobile = page.width < 768
    
    # Variables pour les filtres
    action_filter = ft.Dropdown(
        label="Filtrer par action",
        width=200 if not is_mobile else page.width - 40,
        options=[
            ft.dropdown.Option("", "Toutes"),
            ft.dropdown.Option("create", "Création"),
            ft.dropdown.Option("update", "Modification"),
            ft.dropdown.Option("delete", "Suppression"),
            ft.dropdown.Option("validate", "Validation"),
            ft.dropdown.Option("refuse", "Refus"),
            ft.dropdown.Option("cancel", "Annulation"),
        ],
        value="",
    )
    
    model_filter = ft.Dropdown(
        label="Filtrer par modèle",
        width=200 if not is_mobile else page.width - 40,
        options=[
            ft.dropdown.Option("", "Tous"),
            ft.dropdown.Option("Reservation", "Réservation"),
            ft.dropdown.Option("Caveau", "Caveau"),
            ft.dropdown.Option("Concession", "Concession"),
            ft.dropdown.Option("Paiement", "Paiement"),
            ft.dropdown.Option("Exhumation", "Exhumation"),
            ft.dropdown.Option("User", "Utilisateur"),
        ],
        value="",
    )
    
    search_field = ft.TextField(
        label="Rechercher",
        width=200 if not is_mobile else page.width - 40,
        hint_text="Nom d'utilisateur, objet...",
    )
    
    message_label = ft.Text("", size=14, color=ft.Colors.GREEN)
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_audits_page(page)
    page.on_resize = on_resize
    
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Audit Logs", size=18, weight=ft.FontWeight.BOLD),
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
    
    def apply_filters(e):
        page.run_task(load_audits, page)
    
    # Barre de filtres
    filters_row = ft.Row([
        action_filter,
        model_filter,
        search_field,
        ft.Button("Filtrer", on_click=apply_filters, bgcolor="#1976D2", color="white"),
        ft.Button("Réinitialiser", on_click=lambda e: reset_filters(), bgcolor=ft.Colors.GREY_400, color="white"),
    ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    
    def reset_filters():
        action_filter.value = ""
        model_filter.value = ""
        search_field.value = ""
        page.run_task(load_audits, page)
    


    async def load_audits(page_ref=None):
        """Charge les logs d'audit avec les filtres actuels"""
        # Utiliser la page passée en paramètre ou celle de la portée externe
        current_page = page_ref if page_ref is not None else page
        
        if current_page is None:
            print("Erreur: page est None")
            return
        
        try:
            params = []
            if action_filter.value:
                params.append(f"action={action_filter.value}")
            if model_filter.value:
                params.append(f"model={model_filter.value}")
            if search_field.value:
                params.append(f"search={search_field.value}")
            
            query = "&".join(params) if params else ""
            endpoint = f"audit/logs?{query}" if query else "audit/logs"
            
            audits = await get_request(endpoint)
            print(f"Audits chargés: {len(audits) if audits else 0}")
            
            if audits and isinstance(audits, list) and len(audits) > 0:
                list_container.content = ft.Column([
                    ft.Row([
                        ft.Text("Audit Logs", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{len(audits)} entrées", size=14, color=ft.Colors.GREY_600),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    build_audits_list(audits, is_mobile),
                ], expand=True)
            else:
                list_container.content = ft.Column([
                    ft.Row([
                        ft.Text("Audit Logs", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("0 entrée", size=14, color=ft.Colors.GREY_600),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    ft.Text("Aucun log d'audit trouvé", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            current_page.update()
            
        except Exception as e:
            print(f"Erreur load_audits: {e}")
            if list_container:
                list_container.content = ft.Text(f"Erreur: {e}", color=ft.Colors.RED)
            try:
                current_page.update()
            except:
                pass


    def build_audits_list(audits, is_mobile):
        items = []
        for a in audits:
            action_colors = {
                "create": ft.Colors.GREEN,
                "update": ft.Colors.BLUE,
                "delete": ft.Colors.RED,
                "validate": ft.Colors.GREEN,
                "refuse": ft.Colors.RED,
                "cancel": ft.Colors.ORANGE,
                "login": ft.Colors.BLUE_400,
                "logout": ft.Colors.GREY_600,
            }
            action_color = action_colors.get(a.get("action", ""), ft.Colors.GREY)
            
            changes_text = ""
            if a.get("changes"):
                changes = a.get("changes", {})
                changes_text = ", ".join([f"{k}: {v}" for k, v in changes.items() if k not in ['date', 'timestamp']])
            
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(a.get("timestamp", "N/A")[:19].replace("T", " "), size=12, color=ft.Colors.GREY_600),
                                ft.Container(
                                    ft.Text(a.get("action", "N/A"), size=11, color=ft.Colors.WHITE),
                                    bgcolor=action_color,
                                    padding=5,
                                    border_radius=10,
                                ),
                            ]),
                            ft.Row([
                                ft.Text(f"{a.get('username', 'Anonyme')}", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(f" {a.get('model_name', 'N/A')}", size=13),
                            ]),
                            ft.Text(f" {a.get('object_repr', 'N/A')}", size=13),
                            ft.Text(f" {changes_text[:100]}..." if len(changes_text) > 100 else f"{changes_text}", size=12, color=ft.Colors.GREY_700),
                            ft.Text(f" {a.get('ip_address', 'N/A')}", size=11, color=ft.Colors.GREY_500),
                        ], spacing=5),
                        padding=10,
                        width=500 if not is_mobile else page.width - 40,
                    )
                )
            )
        
        return ft.Row(
            items,
            wrap=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            run_spacing=15,
            height=500,
        )
    
    # Construction de la page
    page.controls.append(
        ft.Column([
            get_header_admin(page, "audits"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Audit Logs", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_audits, page), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    filters_row,
                    ft.Divider(height=10),
                    list_container,
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                expand=True,
                padding=15 if is_mobile else 20,
                bgcolor=ft.Colors.GREY_50,
            )
        ], expand=True, spacing=0)
    )
    page.update()
    
    # Chargement initial
    page.run_task(load_audits)