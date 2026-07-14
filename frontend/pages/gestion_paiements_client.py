import flet as ft
from utils.api import (
    get_paiements_reservation, 
    create_paiement,
    get_reservations,
    get_paiement,
    logout
)
from utils.session import session


# HEADER CLIENT (réutilisé)

def get_header_client(page: ft.Page, active_item: str = ""):
    from pages.dashboard_client import get_header_client as header_client
    return header_client(page, active_item)


def navigate_to(page: ft.Page, destination: str):
    from pages.dashboard_client import navigate_to as nav_to
    nav_to(page, destination)


# PAGE GESTION DES PAIEMENTS (CLIENT)

def gestion_paiements_client_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    page.title = "Mes paiements"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_paiements_client_page(page)
    page.on_resize = on_resize
    
    # ============================================
    # FORMULAIRE DE PAIEMENT
    # ============================================
    
    reservation_dropdown = ft.Dropdown(
        label="Reservation validee",
        width=400 if not is_mobile else page.width - 40,
        options=[],
        value=None,
    )
    
    montant_field = ft.TextField(
        label="Montant (FCFA)",
        width=400 if not is_mobile else page.width - 40,
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="Ex: 500000",
    )
    
    methode_dropdown = ft.Dropdown(
        label="Mode de paiement",
        width=400 if not is_mobile else page.width - 40,
        options=[
            ft.dropdown.Option("mtn_money", "MTN Mobile Money"),
            ft.dropdown.Option("airtel_money", "Airtel Money"),
            ft.dropdown.Option("virement", "Virement bancaire"),
        ],
        value="mtn_money",
    )
    
    numero_field = ft.TextField(
        label="Numero de telephone (9-10 chiffres)",
        width=400 if not is_mobile else page.width - 40,
        hint_text="Ex: 0612345678",
        keyboard_type=ft.KeyboardType.PHONE,
        visible=True,
    )
    
    reference_field = ft.TextField(
        label="Reference de virement",
        width=400 if not is_mobile else page.width - 40,
        hint_text="Ex: VIR-2026-001",
        visible=False,
    )
    
    notes_field = ft.TextField(
        label="Notes (optionnel)",
        width=400 if not is_mobile else page.width - 40,
        multiline=True,
        min_lines=2,
        max_lines=4,
    )
    
    # ✅ Messages simples (labels)
    message = ft.Text("", color=ft.Colors.RED, size=14)
    success_message = ft.Text("", color=ft.Colors.GREEN, size=14)
    
    def on_methode_change(e):
        methode = methode_dropdown.value
        numero_field.visible = False
        reference_field.visible = False
        
        if methode in ["mtn_money", "airtel_money"]:
            numero_field.visible = True
            numero_field.label = "Numero de telephone (9-10 chiffres)"
        elif methode == "virement":
            reference_field.visible = True
        
        page.update()
    
    methode_dropdown.on_change = on_methode_change
    
    def on_submit(e):
        # Vider les messages précédents
        message.value = ""
        success_message.value = ""
        
        if not reservation_dropdown.value:
            message.value = "Veuillez selectionner une reservation"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not montant_field.value:
            message.value = "Veuillez saisir un montant"
            message.color = ft.Colors.RED
            page.update()
            return
        
        try:
            montant = float(montant_field.value)
            if montant <= 0:
                message.value = "Le montant doit etre superieur a 0"
                message.color = ft.Colors.RED
                page.update()
                return
        except ValueError:
            message.value = "Montant invalide"
            message.color = ft.Colors.RED
            page.update()
            return
        
        methode = methode_dropdown.value
        
        if methode in ["mtn_money", "airtel_money"]:
            if not numero_field.value:
                message.value = "Veuillez saisir le numero de telephone"
                message.color = ft.Colors.RED
                page.update()
                return
            if len(numero_field.value) < 9:
                message.value = "Le numero doit contenir au moins 9 chiffres"
                message.color = ft.Colors.RED
                page.update()
                return
        
        data = {
            "reservation_id": int(reservation_dropdown.value),
            "montant": montant,
            "methode": methode,
            "notes": notes_field.value or "",
        }
        
        if methode in ["mtn_money", "airtel_money"]:
            data["numero_telephone"] = numero_field.value
            data["operateur"] = "MTN" if methode == "mtn_money" else "Airtel"
        elif methode == "virement":
            data["numero_transaction"] = reference_field.value or ""
        
        page.run_task(handle_create_paiement, page, data)
    
    async def handle_create_paiement(page: ft.Page, data: dict):
        try:
            result = await create_paiement(data)
            print(f"Resultat paiement: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message.value = result["error"]
                    message.color = ft.Colors.RED
                    page.update()
                    return
                if "id" in result:
                    success_message.value = f"Paiement enregistre - Ref: {result.get('reference_transaction', 'N/A')}"
                    success_message.color = ft.Colors.GREEN
                    montant_field.value = ""
                    numero_field.value = ""
                    reference_field.value = ""
                    notes_field.value = ""
                    message.value = ""
                    page.update()
                    await load_paiements()
                    return
            
            message.value = "Erreur lors de l'enregistrement"
            message.color = ft.Colors.RED
            page.update()
            
        except Exception as e:
            print(f"Erreur: {e}")
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    # ============================================
    # LISTE DES PAIEMENTS
    # ============================================
    
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Mes paiements", size=18, weight=ft.FontWeight.BOLD),
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
            print(f"Erreur chargement reservations: {e}")
    
    def build_paiements_list(paiements):
        if not paiements:
            return ft.Column([
                ft.Text("Aucun paiement", size=16, color=ft.Colors.GREY_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        items = []
        for p in paiements:
            statut = p.get("statut", "inconnu")
            if statut == "valide":
                color = ft.Colors.GREEN
                statut_text = "Valide"
            elif statut == "refuse":
                color = ft.Colors.RED
                statut_text = "Refuse"
            elif statut == "echoue":
                color = ft.Colors.RED
                statut_text = "Echoue"
            else:
                color = ft.Colors.ORANGE
                statut_text = "En attente"
            
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(p.get("reference_transaction", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(ft.Text(statut_text, size=11, color=ft.Colors.WHITE), bgcolor=color, padding=5, border_radius=5),
                            ]),
                            ft.Text(f"Montant: {p.get('montant', 0):,.0f} FCFA"),
                            ft.Text(f"Date: {p.get('date_paiement', 'N/A')[:10] if p.get('date_paiement') else 'N/A'}"),
                            ft.Button("Facture", on_click=lambda e, pid=p['id']: telecharger_facture(page, pid), bgcolor="#1976D2", color="white", disabled=statut != "valide"),
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
    
    async def telecharger_facture(page: ft.Page, paiement_id: int):
        try:
            result = await get_paiement(paiement_id)
            print(f"Resultat facture: {result}")

            if result and isinstance(result, dict):
                if "error" in result:
                    message.value = result["error"]
                    message.color = ft.Colors.RED
                    page.update()
                    return
                if result.get("facture_pdf"):
                    import webbrowser
                    url = f"http://127.0.0.1:8000{result['facture_pdf']}"
                    webbrowser.open(url)
                    success_message.value = "Facture telechargee"
                    success_message.color = ft.Colors.GREEN
                    page.update()
                else:
                    message.value = "Facture non disponible"
                    message.color = ft.Colors.ORANGE
                    page.update()
        except Exception as e:
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    async def load_paiements():
        try:
            user = session.get("user")
            if not user:
                return

            reservations = await get_reservations()
            all_paiements = []
            
            for r in reservations:
                if r.get("client_id") == user.get("id"):
                    paiements = await get_paiements_reservation(r["id"])
                    if paiements and isinstance(paiements, list):
                        all_paiements.extend(paiements)
            
            print(f"Paiements charges: {len(all_paiements) if all_paiements else 0}")

            if all_paiements and len(all_paiements) > 0:
                list_container.content = ft.Column([
                    ft.Text("Mes paiements", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    build_paiements_list(all_paiements),
                ], expand=True)
            else:
                list_container.content = ft.Column([
                    ft.Text("Mes paiements", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.Text("Aucun paiement effectue", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            page.update()

        except Exception as e:
            print(f"Erreur chargement paiements: {e}")
            list_container.content = ft.Column([
                ft.Text("Mes paiements", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
            ])
            page.update()
    
    
    async def load_all():
        await load_reservations()
        await load_paiements()
    
    # ============================================
    # FORMULAIRE
    # ============================================
    
    def on_reset(e):
        montant_field.value = ""
        numero_field.value = ""
        reference_field.value = ""
        notes_field.value = ""
        message.value = ""
        success_message.value = ""
        methode_dropdown.value = "mtn_money"
        on_methode_change(None)
        page.update()

    formulaire = ft.Container(
        content=ft.Column([
            ft.Text("Nouveau paiement", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
            ft.Divider(height=10),
            reservation_dropdown,
            montant_field,
            methode_dropdown,
            numero_field,
            reference_field,
            notes_field,
            message,
            success_message,
            ft.Row([
                ft.Button("Reinitialiser", on_click=on_reset, bgcolor=ft.Colors.GREY_400, color="white", expand=is_mobile),
                ft.Button("Payer", on_click=on_submit, bgcolor="#4CAF50", color="white", expand=is_mobile),
            ], spacing=10),
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
            get_header_client(page, "paiements"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Mes paiements", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_all), bgcolor="#1976D2", color="white"),
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