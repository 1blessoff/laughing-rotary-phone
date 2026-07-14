import flet as ft
from utils.api import get_request, post_request, put_request, delete_request
from utils.session import session


# HEADER ADMIN (réutilisé)

def get_header_admin(page: ft.Page, active_item: str = ""):
    from pages.dashboard_admin import get_header_admin as header_admin
    return header_admin(page, active_item)


def navigate_to(page: ft.Page, destination: str):
    from pages.dashboard_admin import navigate_to as nav_to
    nav_to(page, destination)


# FONCTIONS UTILES

def close_dialog(page: ft.Page):
    if page.dialog:
        page.dialog.open = False
        page.update()


def show_snackbar(page: ft.Page, message: str, color):
    page.snack_bar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=color,
        duration=3000,
        open=True,
    )
    page.update()


# PAGE GESTION DES CATEGORIES

def gestion_categories_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    page.title = "Gestion des categories"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_categories_page(page)
    page.on_resize = on_resize
    
    # Variables du formulaire
    form_mode = ft.Text("Ajouter une categorie", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
    edit_id = ft.Text("", visible=False)
    
    # Champs du formulaire
    nom_field = ft.TextField(label="Nom de la categorie", width=400 if not is_mobile else page.width - 40)
    largeur_field = ft.TextField(label="Largeur (m)", width=400 if not is_mobile else page.width - 40, keyboard_type=ft.KeyboardType.NUMBER)
    longueur_field = ft.TextField(label="Longueur (m)", width=400 if not is_mobile else page.width - 40, keyboard_type=ft.KeyboardType.NUMBER)
    prix_field = ft.TextField(label="Prix de base (FCFA)", width=400 if not is_mobile else page.width - 40, keyboard_type=ft.KeyboardType.NUMBER)
    
    message = ft.Text("", color=ft.Colors.RED)
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Liste des categories", size=18, weight=ft.FontWeight.BOLD),
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
    
    def reset_form():
        nom_field.value = ""
        largeur_field.value = ""
        longueur_field.value = ""
        prix_field.value = ""
        edit_id.visible = False
        edit_id.value = ""
        form_mode.value = "Ajouter une categorie"
        form_mode.color = ft.Colors.BLUE_900
        message.value = ""
        page.update()
    
    def update_form_for_edit(categorie):
        edit_id.value = str(categorie["id"])
        edit_id.visible = True
        nom_field.value = categorie["nom"]
        largeur_field.value = str(categorie["largeur"])
        longueur_field.value = str(categorie["longueur"])
        prix_field.value = str(categorie["prix_base"])
        form_mode.value = f"Modifier: {categorie['nom']}"
        form_mode.color = ft.Colors.ORANGE_900
        message.value = ""
        page.update()
    
    # ============================================
    # CHARGER LA LISTE
    # ============================================
    
    async def load_list():
        try:
            categories = await get_request("caveaux/categories")
            print(f"Categories chargees: {len(categories) if categories else 0}")
            
            if categories and isinstance(categories, list):
                session.set("categories_cache", categories)
                list_container.content = build_categories_list(categories, is_mobile)
            else:
                list_container.content = build_empty_list()
            page.update()
        except Exception as e:
            print(f"Erreur load_list categories: {e}")
            list_container.content = ft.Text(f"Erreur: {e}", color=ft.Colors.RED)
            page.update()
    
    def build_empty_list():
        return ft.Column([
            ft.Text("Aucune categorie trouvee", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Ajoutez votre premiere categorie avec le formulaire ci-dessus", size=14, color=ft.Colors.GREY_600),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    
    def build_categories_list(categories, is_mobile):
        if not categories:
            return build_empty_list()
        
        items = []
        for c in categories:
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c["nom"], size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(f"ID: {c['id']}", size=11, color=ft.Colors.WHITE),
                                    bgcolor=ft.Colors.GREY_600,
                                    padding=5,
                                    border_radius=10,
                                ),
                            ]),
                            ft.Row([
                                ft.Text(f"📐 {c['largeur']} x {c['longueur']} m²", size=13),
                                ft.Text(f"💰 {c['prix_base']:,.0f} FCFA", size=13, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Row([
                                ft.Button("Modifier", on_click=lambda e, cid=c['id']: load_categorie_for_edit(page, cid), 
                                          bgcolor="#1976D2", color="white", expand=is_mobile),
                                ft.Button("Supprimer", on_click=lambda e, cid=c['id']: page.run_task(handle_delete_categorie, page, cid), 
                                          bgcolor="#F44336", color="white", expand=is_mobile),
                            ], spacing=5),
                        ]),
                        padding=10,
                        width=300 if not is_mobile else page.width - 40,
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
    
    def load_categorie_for_edit(page: ft.Page, categorie_id: int):
        categories = session.get("categories_cache", [])
        categorie = next((c for c in categories if c["id"] == categorie_id), None)
        if categorie:
            update_form_for_edit(categorie)
        else:
            show_snackbar(page, "Categorie non trouvee", ft.Colors.RED)
    
    # ============================================
    # SUPPRESSION DIRECTE (SANS DIALOGUE)
    # ============================================
    
    async def handle_delete_categorie(page: ft.Page, categorie_id: int):
        try:
            print(f"🔴 Suppression directe categorie ID: {categorie_id}")
            result = await delete_request(f"caveaux/categories/{categorie_id}")
            print(f"RESULT: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                if "success" in result or "message" in result:
                    show_snackbar(page, "✅ Categorie supprimee", ft.Colors.GREEN)
                    await load_list()
                    return
            
            show_snackbar(page, "Erreur lors de la suppression", ft.Colors.RED)
            
        except Exception as e:
            print(f"Exception: {e}")
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # ============================================
    # CREER / MODIFIER
    # ============================================
    
    def on_submit(e):
        if not nom_field.value:
            message.value = "Veuillez saisir un nom"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, "Veuillez saisir un nom", ft.Colors.RED)
            return
        
        if not largeur_field.value:
            message.value = "Veuillez saisir une largeur"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, "Veuillez saisir une largeur", ft.Colors.RED)
            return
        
        if not longueur_field.value:
            message.value = "Veuillez saisir une longueur"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, "Veuillez saisir une longueur", ft.Colors.RED)
            return
        
        if not prix_field.value:
            message.value = "Veuillez saisir un prix"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, "Veuillez saisir un prix", ft.Colors.RED)
            return
        
        try:
            data = {
                "nom": nom_field.value,
                "largeur": float(largeur_field.value),
                "longueur": float(longueur_field.value),
                "prix_base": float(prix_field.value),
            }
        except ValueError:
            message.value = "Veuillez saisir des nombres valides"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, "Veuillez saisir des nombres valides", ft.Colors.RED)
            return
        
        if edit_id.visible and edit_id.value:
            page.run_task(handle_update_categorie, page, int(edit_id.value), data)
        else:
            page.run_task(handle_create_categorie, page, data)
    
    async def handle_create_categorie(page: ft.Page, data: dict):
        try:
            print(f"=== handle_create_categorie ===")
            print(f"Data: {data}")
            
            result = await post_request("caveaux/categories", data)
            print(f"Result: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message.value = result["error"]
                    message.color = ft.Colors.RED
                    page.update()
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                
                if "id" in result:
                    reset_form()
                    await load_list()
                    show_snackbar(page, f"✅ Categorie {data['nom']} creee", ft.Colors.GREEN)
                    return
            
            message.value = "Erreur inconnue lors de la creation"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, "Erreur inconnue", ft.Colors.RED)
            
        except Exception as e:
            print(f"Exception: {e}")
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    async def handle_update_categorie(page: ft.Page, categorie_id: int, data: dict):
        try:
            print(f"=== handle_update_categorie: {categorie_id} ===")
            print(f"Data: {data}")
            
            result = await put_request(f"caveaux/categories/{categorie_id}", data)
            print(f"Result: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message.value = result["error"]
                    message.color = ft.Colors.RED
                    page.update()
                    show_snackbar(page, result["error"], ft.Colors.RED)
                    return
                
                if "id" in result:
                    reset_form()
                    await load_list()
                    show_snackbar(page, f"✅ Categorie {data['nom']} modifiee", ft.Colors.GREEN)
                    return
            
            message.value = "Erreur inconnue lors de la modification"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, "Erreur inconnue", ft.Colors.RED)
            
        except Exception as e:
            print(f"Exception: {e}")
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # ============================================
    # FORMULAIRE
    # ============================================
    
    formulaire = ft.Container(
        content=ft.Column([
            form_mode,
            ft.Divider(height=10),
            nom_field,
            largeur_field,
            longueur_field,
            prix_field,
            edit_id,
            ft.Row([
                ft.Button("Annuler", on_click=lambda e: reset_form(), bgcolor=ft.Colors.GREY_400, color="white", expand=is_mobile),
                ft.Button("Enregistrer", on_click=on_submit, bgcolor="#4CAF50", color="white", expand=is_mobile),
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
            get_header_admin(page, "categories"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des categories", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_list), bgcolor="#1976D2", color="white"),
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
    
    # Chargement initial
    page.run_task(load_list)