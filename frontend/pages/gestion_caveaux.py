import flet as ft
from utils.api import (
    get_caveaux,
    create_caveau,
    update_caveau,
    delete_caveau,
    changer_statut_caveau,
    logout,
    get_request
)
from utils.session import session

# ============================================
# COORDONNEES DES VILLES
# ============================================

VILLES = {
    "Brazzaville": {"latitude": -4.2634, "longitude": 15.2429},
    "Pointe-Noire": {"latitude": -4.7692, "longitude": 11.8664},
    "Dolisie": {"latitude": -4.2045, "longitude": 12.6686},
    "Nkayi": {"latitude": -4.1667, "longitude": 13.2833},
    "Ouesso": {"latitude": 1.6134, "longitude": 16.0515},
    "Impfondo": {"latitude": 1.6182, "longitude": 18.0586},
    "Sibiti": {"latitude": -3.6833, "longitude": 13.3500},
    "Gamboma": {"latitude": -1.8764, "longitude": 15.8642},
}

# ============================================
# COULEURS PAR STATUT
# ============================================

def get_statut_color(statut: str):
    colors = {
        "disponible": ft.Colors.GREEN,
        "reserve": ft.Colors.ORANGE,
        "occupe": ft.Colors.RED,
        "non_exploitable": ft.Colors.GREY_400,
    }
    return colors.get(statut, ft.Colors.GREY)

def get_statut_emoji(statut: str):
    emojis = {
        "disponible": "🟢",
        "reserve": "🟠",
        "occupe": "🔴",
        "non_exploitable": "⚪",
    }
    return emojis.get(statut, "⚪")


# ============================================
# HEADER ADMIN
# ============================================

def get_header_admin(page: ft.Page, active_item: str = ""):
    user = session.get("user", {})
    username = user.get("username", "Admin")
    role = user.get("role", "admin")
    
    def on_logout(e):
        page.run_task(handle_logout)
    
    async def handle_logout():
        await logout()
        session.clear()
        from pages.auth import login_page
        login_page(page)
    
    is_mobile = page.width < 768
    
    menu_items = [
        ft.TextButton("Dashboard", on_click=lambda e: navigate_to(page, "dashboard"),
                      style=ft.ButtonStyle(color="white" if active_item!="dashboard" else "#4FC3F7")),
        ft.TextButton("Caveaux", on_click=lambda e: navigate_to(page, "caveaux"),
                      style=ft.ButtonStyle(color="white" if active_item!="caveaux" else "#4FC3F7")),
        ft.TextButton("Reservations", on_click=lambda e: navigate_to(page, "reservations"),
                      style=ft.ButtonStyle(color="white" if active_item!="reservations" else "#4FC3F7")),
        ft.TextButton("Paiements", on_click=lambda e: navigate_to(page, "paiements"),
                      style=ft.ButtonStyle(color="white" if active_item!="paiements" else "#4FC3F7")),
        ft.TextButton("Concessions", on_click=lambda e: navigate_to(page, "concessions"),
                      style=ft.ButtonStyle(color="white" if active_item!="concessions" else "#4FC3F7")),
        ft.TextButton("Exhumations", on_click=lambda e: navigate_to(page, "exhumations"),
                      style=ft.ButtonStyle(color="white" if active_item!="exhumations" else "#4FC3F7")),
        ft.TextButton("Utilisateurs", on_click=lambda e: navigate_to(page, "users"),
                      style=ft.ButtonStyle(color="white" if active_item!="users" else "#4FC3F7")),
    ]
    
    if not is_mobile:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Administration", size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row(menu_items, spacing=10),
                        ft.Row([
                            ft.Text(f"{username} ({role})", size=12, color="white"),
                            ft.TextButton("Deconnexion", on_click=on_logout, style=ft.ButtonStyle(color="white")),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#21273A",
                ),
            ], spacing=0),
            width=page.width,
        )
    else:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Admin", size=18, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row([
                            ft.Text(f"{username}", size=12, color="white"),
                            ft.PopupMenuButton(
                                icon=None,
                                content=ft.Text("Menu", color="white"),
                                items=[
                                    ft.PopupMenuItem(content=ft.Text("Dashboard"), on_click=lambda e: navigate_to(page, "dashboard")),
                                    ft.PopupMenuItem(content=ft.Text("Caveaux"), on_click=lambda e: navigate_to(page, "caveaux")),
                                    ft.PopupMenuItem(content=ft.Text("Reservations"), on_click=lambda e: navigate_to(page, "reservations")),
                                    ft.PopupMenuItem(content=ft.Text("Paiements"), on_click=lambda e: navigate_to(page, "paiements")),
                                    ft.PopupMenuItem(content=ft.Text("Concessions"), on_click=lambda e: navigate_to(page, "concessions")),
                                    ft.PopupMenuItem(content=ft.Text("Exhumations"), on_click=lambda e: navigate_to(page, "exhumations")),
                                    ft.PopupMenuItem(content=ft.Text("Utilisateurs"), on_click=lambda e: navigate_to(page, "users")),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(content=ft.Text("Deconnexion"), on_click=on_logout),
                                ],
                            ),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=14,
                    bgcolor="#21273A",
                ),
            ], spacing=0),
            width=page.width,
        )


def navigate_to(page: ft.Page, destination: str):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    if destination == "dashboard":
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)
    elif destination == "caveaux":
        gestion_caveaux_page(page)
    elif destination == "users":
        from pages.gestion_utilisateurs import gestion_utilisateurs_page
        gestion_utilisateurs_page(page)
    elif destination == "categories":
        from pages.gestion_categories import gestion_categories_page
        gestion_categories_page(page)
    elif destination == "reservations":
        from pages.dashboard_admin import reservations_page
        reservations_page(page)
    elif destination == "paiements":
        from pages.gestion_paiements import gestion_paiements_page
        gestion_paiements_page(page)
    elif destination == "concessions":
        from pages.dashboard_admin import concessions_page
        concessions_page(page)
    elif destination == "exhumations":
        from pages.dashboard_admin import exhumations_page
        exhumations_page(page)
    else:
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)


# ============================================
# PAGE GESTION DES CAVEAUX
# ============================================

def gestion_caveaux_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    page.title = "Gestion des caveaux"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_caveaux_page(page)
    page.on_resize = on_resize
    
    # Variables du formulaire
    form_mode = ft.Text("Ajouter un caveau", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
    edit_id = ft.Text("", visible=False)
    edit_ref = ft.Text("", visible=False)
    
    # Champs simplifiés
    ville_dropdown = ft.Dropdown(
        label="Ville",
        width=400 if not is_mobile else page.width - 40,
        options=[ft.dropdown.Option(v, v) for v in VILLES.keys()],
        value="Brazzaville",
    )
    
    section_dropdown = ft.Dropdown(
        label="Section",
        width=400 if not is_mobile else page.width - 40,
        options=[ft.dropdown.Option("A", "Section A"), ft.dropdown.Option("B", "Section B"), 
                 ft.dropdown.Option("C", "Section C"), ft.dropdown.Option("D", "Section D")],
        value="A",
    )
    
    numero_field = ft.TextField(
        label="Numero (auto-genere si vide)",
        width=400 if not is_mobile else page.width - 40,
        hint_text="Ex: 001, 002...",
    )
    
    reference_preview = ft.Text("Reference: A-001", size=14, color=ft.Colors.GREY_600)
    
    def update_reference(e):
        section = section_dropdown.value or "A"
        numero = numero_field.value or "001"
        ref = f"{section}-{numero.zfill(3)}"
        reference_preview.value = f"Reference: {ref}"
        page.update()
    
    section_dropdown.on_change = update_reference
    numero_field.on_change = update_reference
    
    # Dropdown categories - sera rempli dynamiquement
    categorie_dropdown = ft.Dropdown(
        label="Categorie",
        width=400 if not is_mobile else page.width - 40,
        options=[],
        value=None,
    )
    
    statut_dropdown = ft.Dropdown(
        label="Statut",
        width=400 if not is_mobile else page.width - 40,
        options=[
            ft.dropdown.Option("disponible", "Disponible"),
            ft.dropdown.Option("reserve", "Reserve"),
            ft.dropdown.Option("occupe", "Occupe"),
            ft.dropdown.Option("non_exploitable", "Non exploitable"),
        ],
        value="disponible",
    )
    
    message = ft.Text("", color=ft.Colors.RED)
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Liste des caveaux", size=18, weight=ft.FontWeight.BOLD),
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
    
    # ============================================
    # FONCTIONS DE GESTION
    # ============================================
    
    def get_next_number(section):
        """Trouver le prochain numero disponible pour une section"""
        caveaux = session.get("caveaux_cache", [])
        if not caveaux:
            return 1
        nums = []
        for c in caveaux:
            ref = c.get("reference", "")
            if ref.startswith(section + "-"):
                try:
                    num = int(ref.split("-")[1])
                    nums.append(num)
                except:
                    pass
        if not nums:
            return 1
        return max(nums) + 1
    
    def update_form_for_edit(caveau):
        """Pre-remplir le formulaire pour modification"""
        ref = caveau.get("reference", "")
        section = ref[0] if ref else "A"
        numero = ref.split("-")[1] if "-" in ref else "001"
        
        section_dropdown.value = section
        numero_field.value = numero
        reference_preview.value = f"Reference: {ref}"
        
        # Trouver la ville par coordonnees
        lat = caveau.get("latitude")
        lng = caveau.get("longitude")
        ville_trouvee = "Brazzaville"
        for v, coords in VILLES.items():
            if abs(coords["latitude"] - lat) < 0.01 and abs(coords["longitude"] - lng) < 0.01:
                ville_trouvee = v
                break
        ville_dropdown.value = ville_trouvee
        
        # Categorie
        cat_id = caveau.get("categorie_id")
        if cat_id:
            categorie_dropdown.value = str(cat_id)
        
        statut_dropdown.value = caveau.get("statut", "disponible")
        edit_id.value = str(caveau.get("id", ""))
        edit_id.visible = True
        edit_ref.value = ref
        form_mode.value = f"Modifier caveau {ref}"
        form_mode.color = ft.Colors.ORANGE_900
        message.value = ""
        page.update()
    
    def reset_form():
        ville_dropdown.value = "Brazzaville"
        section_dropdown.value = "A"
        numero_field.value = ""
        if categorie_dropdown.options:
            categorie_dropdown.value = categorie_dropdown.options[0].key
        statut_dropdown.value = "disponible"
        edit_id.visible = False
        edit_id.value = ""
        edit_ref.value = ""
        form_mode.value = "Ajouter un caveau"
        form_mode.color = ft.Colors.BLUE_900
        message.value = ""
        update_reference(None)
        page.update()
    
    # ============================================
    # CHARGER LES CATEGORIES DEPUIS L'API
    # ============================================
    
    async def charger_categories():
        """Charge les categories depuis l'API"""
        try:
            categories = await get_request("caveaux/categories")
            print(f"Categories chargees: {categories}")
            
            if categories and isinstance(categories, list):
                options = []
                for c in categories:
                    if isinstance(c, dict) and "id" in c:
                        label = f"{c.get('nom', 'Sans nom')} ({c.get('largeur', 0)}x{c.get('longueur', 0)}m²)"
                        options.append(ft.dropdown.Option(str(c["id"]), label))
                
                categorie_dropdown.options = options
                if options:
                    categorie_dropdown.value = options[0].key
                page.update()
                return categories
            return []
        except Exception as e:
            print(f"Erreur chargement categories: {e}")
            return []
    
    # ============================================
    # CREER/MODIFIER/SUPPRIMER
    # ============================================
    
    def on_submit(e):
        if not section_dropdown.value:
            message.value = "Veuillez selectionner une section"
            message.color = ft.Colors.RED
            page.update()
            return
        
        # Generer la reference
        section = section_dropdown.value
        if numero_field.value:
            numero = numero_field.value.zfill(3)
        else:
            next_num = get_next_number(section)
            numero = str(next_num).zfill(3)
        
        reference = f"{section}-{numero}"
        
        # Verifier si la reference existe deja (sauf en modification)
        if not (edit_id.visible and edit_id.value) or reference != edit_ref.value:
            caveaux = session.get("caveaux_cache", [])
            if any(c["reference"] == reference for c in caveaux):
                message.value = f"La reference {reference} existe deja"
                message.color = ft.Colors.RED
                page.update()
                return
        
        # Coordonnees GPS avec variation aleatoire
        ville = ville_dropdown.value
        coords = VILLES.get(ville, VILLES["Brazzaville"])
        
        import random
        latitude = coords["latitude"] + random.uniform(-0.005, 0.005)
        longitude = coords["longitude"] + random.uniform(-0.005, 0.005)
        
        # Categorie
        cat_id = int(categorie_dropdown.value) if categorie_dropdown.value else 1
        
        data = {
            "reference": reference,
            "section": section,
            "bloc": f"BLOC-{section}",
            "allee": f"ALLEE-{section}",
            "latitude": latitude,
            "longitude": longitude,
            "superficie": 4.0,
            "categorie_id": cat_id,
            "statut": statut_dropdown.value,
        }
        
        if edit_id.visible and edit_id.value:
            page.run_task(handle_update_caveau, page, int(edit_id.value), data)
        else:
            page.run_task(handle_create_caveau, page, data)














    async def handle_create_caveau(page: ft.Page, data: dict):
        try:
            print(f"=== handle_create_caveau ===")
            print(f"Data: {data}")
            
            result = await create_caveau(data)
            print(f"Result: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message.value = result["error"]
                    message.color = ft.Colors.RED
                    page.update()
                    return
                
                if "id" in result:
                    reset_form()
                    await load_list()
                    show_snackbar(page, "Caveau cree avec succes", ft.Colors.GREEN)
                    return
            
            message.value = "Erreur inconnue lors de la creation"
            message.color = ft.Colors.RED
            page.update()
            
        except Exception as e:
            print(f"Exception: {e}")
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    async def handle_update_caveau(page: ft.Page, caveau_id: int, data: dict):
        try:
            result = await update_caveau(caveau_id, data)
            if result and isinstance(result, dict) and "error" in result:
                message.value = result["error"]
                message.color = ft.Colors.RED
                page.update()
                return
            reset_form()
            await load_list()
            show_snackbar(page, "Caveau modifie avec succes", ft.Colors.GREEN)
        except Exception as e:
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    # ✅ SUPPRESSION DIRECTE SANS DIALOGUE
    async def handle_delete_caveau(page: ft.Page, caveau_id: int):
        print(f"🔴 Suppression directe ID: {caveau_id}")
        try:
            result = await delete_caveau(caveau_id)
            print(f"RESULT: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, f"Erreur: {result['error']}", ft.Colors.RED)
                    return
                if "success" in result:
                    show_snackbar(page, "✅ Caveau supprime", ft.Colors.GREEN)
                    await load_list()
                    return
            
            show_snackbar(page, "Erreur lors de la suppression", ft.Colors.RED)
            
        except Exception as e:
            print(f"EXCEPTION: {e}")
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # ✅ CHANGEMENT DE STATUT DIRECT (cycle)
    async def handle_change_statut(page: ft.Page, caveau_id: int):
        # Cycle des statuts
        statuts = ["disponible", "reserve", "occupe", "non_exploitable"]
        
        # Récupérer le statut actuel du caveau
        caveaux = session.get("caveaux_cache", [])
        caveau = next((c for c in caveaux if c["id"] == caveau_id), None)
        statut_actuel = caveau.get("statut", "disponible") if caveau else "disponible"
        
        # Trouver le prochain statut
        try:
            index = statuts.index(statut_actuel)
            nouveau_statut = statuts[(index + 1) % len(statuts)]
        except ValueError:
            nouveau_statut = "disponible"
        
        print(f"🔴 Changement statut: {statut_actuel} -> {nouveau_statut}")
        
        try:
            result = await changer_statut_caveau(caveau_id, nouveau_statut)
            print(f"RESULT: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    show_snackbar(page, f"Erreur: {result['error']}", ft.Colors.RED)
                    return
                if "success" in result:
                    show_snackbar(page, f"Statut: {nouveau_statut}", ft.Colors.GREEN)
                    await load_list()
                    return
            
            show_snackbar(page, "Erreur changement statut", ft.Colors.RED)
            
        except Exception as e:
            print(f"EXCEPTION: {e}")
            show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)
    
    # ============================================
    # CHARGER LA LISTE DES CAVEAUX
    # ============================================
    
    async def load_list():
        try:
            caveaux = await get_caveaux()
            print(f"Caveaux recuperes: {len(caveaux) if caveaux else 0}")
            
            if caveaux and isinstance(caveaux, list):
                session.set("caveaux_cache", caveaux)
                list_container.content = build_caveaux_list(caveaux, is_mobile)
            else:
                list_container.content = build_empty_list()
            page.update()
        except Exception as e:
            print(f"Erreur load_list: {e}")
            list_container.content = ft.Text(f"Erreur: {e}", color=ft.Colors.RED)
            page.update()
    
    def build_empty_list():
        return ft.Column([
            ft.Text("📭 Aucun caveau trouve", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Ajoutez votre premier caveau avec le formulaire ci-dessus", size=14, color=ft.Colors.GREY_600),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    
    def build_caveaux_list(caveaux, is_mobile):
        if not caveaux:
            return build_empty_list()
        
        items = []
        for c in caveaux:
            color = get_statut_color(c.get("statut", "disponible"))

            # Récupérer le prix depuis la catégorie du caveau
            prix_value = c.get("prix_base")
            if prix_value is None:
                prix_value = c.get("prix", 0)
            try:
                prix = float(prix_value)
            except (TypeError, ValueError):
                prix = 0
            prix_affichage = f"{prix:,.0f} FCFA" if prix > 0 else "Prix non défini"

            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c.get("reference", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(f"{c.get('statut', 'disponible')}", size=12, color="white"),
                                    bgcolor=color,
                                    padding=10,
                                    border_radius=5,
                                ),
                            ]),
                            ft.Text(f"Section: {c.get('section', 'N/A')} - Bloc: {c.get('bloc', 'N/A')}"),
                            ft.Text(f"Categorie: {c.get('categorie_nom', 'N/A')} - {prix_affichage}"),
                            
                            ft.Row([
                                ft.Button("Modifier", on_click=lambda e, cid=c['id']: load_caveau_for_edit(page, cid), 
                                          bgcolor="#13589C", color="white", expand=is_mobile),
                                ft.Button("Statut", on_click=lambda e, cid=c['id']: page.run_task(handle_change_statut, page, cid), 
                                          bgcolor="#15A82D", color="white", expand=is_mobile),
                                ft.Button("Supprimer", on_click=lambda e, cid=c['id']: page.run_task(handle_delete_caveau, page, cid), 
                                          bgcolor="#A72C23", color="white", expand=is_mobile),
                            ], spacing=5),
                        ]),
                        padding=15,
                        width=450 if not is_mobile else page.width - 40,
                    )
                )
            )
        
        return ft.Row(
            items, 
            wrap=True, 
            scroll=ft.ScrollMode.AUTO, 
            height=500, 
            run_spacing=15, 
            spacing=15,
        )
    
    def load_caveau_for_edit(page: ft.Page, caveau_id: int):
        caveaux = session.get("caveaux_cache", [])
        caveau = next((c for c in caveaux if c["id"] == caveau_id), None)
        if caveau:
            update_form_for_edit(caveau)
        else:
            show_snackbar(page, "Caveau non trouve", ft.Colors.RED)

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
    
    # ============================================
    # FORMULAIRE
    # ============================================
    
    formulaire = ft.Container(
        content=ft.Column([
            form_mode,
            ft.Divider(height=10),
            ville_dropdown,
            section_dropdown,
            numero_field,
            reference_preview,
            categorie_dropdown,
            statut_dropdown,
            edit_id,
            edit_ref,
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
            get_header_admin(page, "caveaux"),
            ft.Container(
                content=ft.Column([
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
    

    # CHARGEMENT INITIAL
    
    # Charger les categories
    page.run_task(charger_categories)
    
    # Charger la liste des caveaux
    page.run_task(load_list)
    update_reference(None)