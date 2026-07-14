import flet as ft
from utils.api import (
    get_concessions,
    create_concession,
    renouveler_concession,
    get_reservations,
    logout
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


# PAGE GESTION DES CONCESSIONS

def gestion_concessions_page(page: ft.Page):
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
    
    page.title = "Gestion des concessions"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_concessions_page(page)
    page.on_resize = on_resize
    
    # ============================================
    # FORMULAIRE DE CREATION
    # ============================================
    
    reservation_dropdown = ft.Dropdown(
        label="Réservation validée",
        width=400 if not is_mobile else page.width - 40,
        options=[],
        value=None,
    )
    
    type_dropdown = ft.Dropdown(
        label="Type de concession",
        width=400 if not is_mobile else page.width - 40,
        options=[
            ft.dropdown.Option("temporaire", "Temporaire"),
            ft.dropdown.Option("perpetuelle", "Perpétuelle"),
        ],
        value="temporaire",
    )
    
    date_debut_field = ft.TextField(
        label="Date de début",
        width=400 if not is_mobile else page.width - 40,
        hint_text="AAAA-MM-JJ",
    )
    
    duree_field = ft.TextField(
        label="Durée (années)",
        width=400 if not is_mobile else page.width - 40,
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="10",
        value="10",
    )
    
    message = ft.Text("", color=ft.Colors.RED)
    
    def on_create(e):
        if not reservation_dropdown.value:
            show_snackbar(page, "Veuillez sélectionner une réservation", ft.Colors.RED)
            return
        
        if not date_debut_field.value:
            show_snackbar(page, "Veuillez saisir une date de début", ft.Colors.RED)
            return
        
        try:
            data = {
                "reservation_id": int(reservation_dropdown.value),
                "type_concession": type_dropdown.value,
                "date_debut": date_debut_field.value,
                "duree_ans": int(duree_field.value),
            }
            page.run_task(handle_create_concession, page, data)
        except ValueError:
            show_snackbar(page, "Durée invalide", ft.Colors.RED)
    
    async def handle_create_concession(page: ft.Page, data: dict):
        try:
            result = await create_concession(data)
            print(f"Résultat concession: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                if "id" in result:
                    show_snackbar(page, f" Concession créée: {result.get('numero_contrat', '')}", ft.Colors.GREEN)
                    date_debut_field.value = ""
                    await load_concessions()
                    await load_reservations()
                    return
            
            show_snackbar(page, "Erreur lors de la création", ft.Colors.RED)
            
        except Exception as e:
            print(f"Erreur: {e}")
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # ============================================
    # LISTE DES CONCESSIONS
    # ============================================
    
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Liste des concessions", size=18, weight=ft.FontWeight.BOLD),
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
    
    async def load_reservations():
        try:
            reservations = await get_reservations()
            valid_reservations = [r for r in reservations if r["statut"] == "validee"]
            
            options = []
            for r in valid_reservations:
                # Vérifier si la réservation a déjà une concession
                try:
                    concessions = await get_concessions()
                    has_concession = any(c["reservation_id"] == r["id"] for c in concessions)
                    if not has_concession:
                        options.append(
                            ft.dropdown.Option(
                                str(r["id"]), 
                                f"#{r['id']} - {r['nom_defunt']} ({r['caveau_reference']})"
                            )
                        )
                except:
                    options.append(
                        ft.dropdown.Option(
                            str(r["id"]), 
                            f"#{r['id']} - {r['nom_defunt']} ({r['caveau_reference']})"
                        )
                    )
            
            reservation_dropdown.options = options
            if options:
                reservation_dropdown.value = options[0].key
            page.update()
        except Exception as e:
            print(f"Erreur chargement réservations: {e}")
    
    def build_concessions_list(concessions):
        if not concessions:
            return ft.Column([
                ft.Text("Aucune concession", size=16, color=ft.Colors.GREY_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        items = []
        for c in concessions:
            est_expiree = c.get("est_expiree", False)
            jours_restants = c.get("jours_restants")
            
            status_color = ft.Colors.RED if est_expiree else ft.Colors.GREEN
            status_text = "Expirée" if est_expiree else f"{jours_restants} jours restants" if jours_restants else "Perpétuelle"
            
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c.get("numero_contrat", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(c.get("type_concession", "N/A"), size=11, color=ft.Colors.WHITE),
                                    bgcolor=ft.Colors.BLUE_700,
                                    padding=5,
                                    border_radius=10,
                                ),
                                ft.Container(
                                    ft.Text(status_text, size=11, color=ft.Colors.WHITE),
                                    bgcolor=status_color,
                                    padding=5,
                                    border_radius=10,
                                ),
                            ]),
                            ft.Text(f"Réservation: #{c.get('reservation_id', 'N/A')}"),
                            ft.Text(f"Début: {c.get('date_debut', 'N/A')}"),
                            ft.Text(f"Fin: {c.get('date_fin', 'Perpétuelle')}"),
                            ft.Row([
                                ft.Button(
                                    "Renouveler",
                                    on_click=lambda e, cid=c['id']: page.run_task(handle_renouveler, page, cid),
                                    bgcolor="#FF9800", color="white",
                                    disabled=c.get("type_concession") == "perpetuelle" or est_expiree,
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
    
    async def handle_renouveler(page: ft.Page, concession_id: int):
        try:
            result = await renouveler_concession(concession_id, {})
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                show_snackbar(page, "Concession renouvelée", ft.Colors.GREEN)
                await load_concessions()
                return
        except Exception as e:
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    async def load_concessions():
        try:
            concessions = await get_concessions()
            print(f"Concessions chargées: {len(concessions) if concessions else 0}")
            
            if concessions and isinstance(concessions, list) and len(concessions) > 0:
                list_container.content = ft.Column([
                    ft.Text("Liste des concessions", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    build_concessions_list(concessions),
                ], expand=True)
            else:
                list_container.content = ft.Column([
                    ft.Text("Liste des concessions", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.Text("Aucune concession", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            page.update()
            
        except Exception as e:
            print(f"Erreur concessions: {e}")
            list_container.content = ft.Text(f"Erreur: {e}", color=ft.Colors.RED)
            page.update()
    
    async def load_all():
        await load_reservations()
        await load_concessions()
    
    # ============================================
    # FORMULAIRE
    # ============================================
    
    formulaire = ft.Container(
        content=ft.Column([
            ft.Text("Nouvelle concession", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
            ft.Divider(height=10),
            reservation_dropdown,
            type_dropdown,
            date_debut_field,
            duree_field,
            ft.Row([
                ft.Button("Réinitialiser", on_click=lambda e: date_debut_field.value, bgcolor=ft.Colors.GREY_400, color="white", expand=is_mobile),
                ft.Button("Créer", on_click=on_create, bgcolor="#4CAF50", color="white", expand=is_mobile),
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
            get_header_admin(page, "concessions"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_all), bgcolor="#1976D2", color="white"),
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