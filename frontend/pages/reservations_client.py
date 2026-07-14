import flet as ft
from utils.api import get_caveaux_disponibles, get_reservations, create_reservation, annuler_reservation, get_reservation
from utils.session import session


# ============================================
# CREER UNE RESERVATION
# ============================================

def create_reservation_page(page: ft.Page):
    from pages.dashboard_client import get_header_client, refresh_current_page, client_dashboard

    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Nouvelle reservation"
    page.controls.clear()
    is_mobile = page.width < 768

    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    page.controls.append(
        ft.Column([
            get_header_client(page, "reservations"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Nouvelle reservation", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10),
                    ft.ProgressRing(),
                    ft.Text("Chargement..."),
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_create_reservation_form, page)


async def load_create_reservation_form(page: ft.Page):
    from pages.dashboard_client import get_header_client, client_dashboard, show_snackbar

    try:
        caveaux = await get_caveaux_disponibles()
        is_mobile = page.width < 768

        if not caveaux:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_client(page, "reservations"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Nouvelle reservation", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.TextButton("Retour", on_click=lambda e: client_dashboard(page)),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Text("Aucun caveau disponible", size=16, color=ft.Colors.GREY_600),
                            ft.Button("Reessayer", on_click=lambda e: page.run_task(load_create_reservation_form, page), bgcolor="#1976D2", color="white"),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    ),
                ], expand=True, spacing=0)
            )
            page.update()
            return

        caveau_options = [
            ft.dropdown.Option(
                key=str(c["id"]),
                text=f"{c['reference']} - Section {c['section']}"
            ) for c in caveaux
        ]

        caveau_dropdown = ft.Dropdown(
            label="Caveau",
            options=caveau_options,
            width=page.width - 40 if is_mobile else 400,
            bgcolor=ft.Colors.WHITE,
            border_color="#1A237E",
            focused_border_color="#1976D2",
        )

        preselected_id = session.get("selected_caveau_id")
        if preselected_id and str(preselected_id) in [opt.key for opt in caveau_options]:
            caveau_dropdown.value = str(preselected_id)
        session.remove("selected_caveau_id")

        nom_defunt = ft.TextField(label="Nom du defunt", width=page.width - 40 if is_mobile else 400)
        prenom_defunt = ft.TextField(label="Prenom du defunt", width=page.width - 40 if is_mobile else 400)
        date_deces = ft.TextField(label="Date de deces (AAAA-MM-JJ)", width=page.width - 40 if is_mobile else 400, hint_text="Ex: 2026-06-20")
        date_enterrement = ft.TextField(label="Date d'enterrement (AAAA-MM-JJ)", width=page.width - 40 if is_mobile else 400, hint_text="Ex: 2026-06-25")
        nom_famille = ft.TextField(label="Nom de la famille", width=page.width - 40 if is_mobile else 400)
        telephone = ft.TextField(label="Telephone", width=page.width - 40 if is_mobile else 400)

        message = ft.Text("", color=ft.Colors.RED)

        def on_submit(e):
            if not session.get("user"):
                message.value = "Votre session a expire, veuillez vous reconnecter."
                message.color = ft.Colors.RED
                page.update()
                from pages.auth import login_page
                login_page(page)
                return

            if not caveau_dropdown.value:
                message.value = "Veuillez selectionner un caveau"
                message.color = ft.Colors.RED
                page.update()
                return
            if not nom_defunt.value:
                message.value = "Veuillez saisir le nom du defunt"
                message.color = ft.Colors.RED
                page.update()
                return
            if not date_deces.value:
                message.value = "Veuillez saisir la date de deces"
                message.color = ft.Colors.RED
                page.update()
                return
            if not date_enterrement.value:
                message.value = "Veuillez saisir la date d'enterrement"
                message.color = ft.Colors.RED
                page.update()
                return

            page.run_task(handle_submit, caveau_dropdown.value, nom_defunt.value, prenom_defunt.value,
                          date_deces.value, date_enterrement.value, nom_famille.value, telephone.value)

        async def handle_submit(caveau_id, nom, prenom, date_deces_val, date_enterrement_val, famille, tel):
            try:
                data = {
                    "caveau_id": int(caveau_id),
                    "nom_defunt": nom,
                    "prenom_defunt": prenom,
                    "date_deces": date_deces_val,
                    "date_enterrement": date_enterrement_val,
                    "nom_famille": famille,
                    "telephone": tel,
                    "besoin_ceremonie": False,
                    "besoin_voiture": False,
                }

                result = await create_reservation(data)
                print(f"Resultat reservation: {result}")

                if not result or "error" in result:
                    erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
                    message.value = erreur
                    message.color = ft.Colors.RED
                    page.update()
                    if "authentifi" in erreur.lower():
                        from pages.auth import login_page
                        login_page(page)
                    return

                show_snackbar(page, "Reservation creee avec succes !", ft.Colors.GREEN)
                mes_reservations_page(page)

            except Exception as e:
                message.value = f"Erreur: {e}"
                message.color = ft.Colors.RED
                page.update()

        form = ft.Container(
            content=ft.Column([
                ft.Text("Nouvelle reservation", size=18, weight=ft.FontWeight.BOLD, color="#1A237E"),
                ft.Divider(height=10),
                caveau_dropdown,
                nom_defunt,
                prenom_defunt,
                date_deces,
                date_enterrement,
                nom_famille,
                telephone,
                message,
                ft.Row([
                    ft.Button("Reserver", on_click=on_submit, bgcolor="#1976D2", color="white"),
                    ft.Button("Annuler", on_click=lambda e: client_dashboard(page), bgcolor=ft.Colors.GREY_400, color="white"),
                ], spacing=10),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=25,
            bgcolor="#3A78D4",
            border_radius=10,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
        )

        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_client(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Nouvelle reservation", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.TextButton("Retour", on_click=lambda e: client_dashboard(page)),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Text(f"{len(caveaux)} caveau(x) disponible(s)", size=14, color=ft.Colors.GREY_600),
                        form,
                    ], scroll=ft.ScrollMode.AUTO, expand=True),
                    expand=True,
                    padding=15 if is_mobile else 20,
                    bgcolor=ft.Colors.GREY_50,
                ),
            ], expand=True, spacing=0)
        )
        page.update()

    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_client(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_create_reservation_form, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


# ============================================
# MES RESERVATIONS
# ============================================

def mes_reservations_page(page: ft.Page):
    from pages.dashboard_client import get_header_client, refresh_current_page

    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Mes reservations"
    page.controls.clear()
    is_mobile = page.width < 768

    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    page.controls.append(
        ft.Column([
            get_header_client(page, "reservations"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Mes reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_mes_reservations, page), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    ft.ProgressRing(),
                    ft.Text("Chargement..."),
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_mes_reservations, page)


async def load_mes_reservations(page: ft.Page):
    from pages.dashboard_client import get_header_client

    try:
        data = await get_reservations()
        is_mobile = page.width < 768

        if not data:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_client(page, "reservations"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Mes reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_mes_reservations, page), bgcolor="#1976D2", color="white"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Text("Aucune reservation", size=16, color=ft.Colors.GREY_600),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    ),
                ], expand=True, spacing=0)
            )
            page.update()
            return

        items = []
        for r in data:
            statut = r.get("statut", "inconnu")
            statut_color = {
                "en_attente": ft.Colors.ORANGE,
                "validee": ft.Colors.GREEN,
                "annulee": ft.Colors.RED,
                "refusee": ft.Colors.RED,
            }.get(statut, ft.Colors.GREY)

            statut_text = {
                "en_attente": "En attente",
                "validee": "Validee",
                "annulee": "Annulee",
                "refusee": "Refusee",
            }.get(statut, statut)

            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(f"Reservation #{r['id']}", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(ft.Text(statut_text, size=12, color="white"), bgcolor=statut_color, padding=5, border_radius=5),
                            ]),
                            ft.Text(f"Defunt: {r.get('nom_defunt', 'N/A')} {r.get('prenom_defunt', '')}"),
                            ft.Text(f"Caveau: {r.get('caveau_reference', 'N/A')}"),
                            ft.Text(f"Date deces: {r.get('date_deces', 'N/A')}", size=12, color=ft.Colors.GREY_600),
                            ft.Text(f"Date enterrement: {r.get('date_enterrement', 'N/A')}", size=12, color=ft.Colors.GREY_600),
                            ft.Row([
                                ft.Button("Annuler", on_click=lambda e, rid=r['id']: page.run_task(annuler_reservation_action, page, rid), bgcolor=ft.Colors.RED, color="white", disabled=(statut not in ["en_attente", "validee"])),
                            ], spacing=10),
                        ], spacing=5),
                        padding=10,
                    ),
                    elevation=2,
                )
            )

        grid = ft.GridView(
            controls=items,
            runs_count=1 if is_mobile else 2 if page.width < 1024 else 3,
            max_extent=400,
            spacing=10,
            run_spacing=10,
            child_aspect_ratio=1.2,
            padding=10,
        )

        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_client(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Mes reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_mes_reservations, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Container(content=grid, expand=True, height=500),
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
                get_header_client(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_mes_reservations, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


def show_snackbar(page: ft.Page, message: str, color):
    page.snack_bar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=color,
        duration=3000,
        open=True,
    )
    page.update()


async def annuler_reservation_action(page: ft.Page, reservation_id: int):
    from pages.dashboard_client import show_snackbar

    try:
        result = await annuler_reservation(reservation_id, "Annulee par le client")
        if not result or "error" in result:
            show_snackbar(page, result.get("error", "Erreur inconnue") if result else "Erreur inconnue", ft.Colors.RED)
            return
        show_snackbar(page, f"Reservation #{reservation_id} annulee", ft.Colors.GREEN)
        await load_mes_reservations(page)
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)