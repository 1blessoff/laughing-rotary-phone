import flet as ft
from utils.api import get_caveaux_disponibles
from utils.session import session


def caveaux_disponibles_page(page: ft.Page):
    from pages.dashboard_client import get_header_client, refresh_current_page

    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Caveaux disponibles"
    page.controls.clear()
    is_mobile = page.width < 768

    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    page.controls.append(
        ft.Column([
            get_header_client(page, "caveaux"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Caveaux disponibles", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_caveaux_disponibles, page), bgcolor="#1976D2", color="white"),
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
    page.run_task(load_caveaux_disponibles, page)


async def load_caveaux_disponibles(page: ft.Page):
    from pages.dashboard_client import get_header_client, navigate_to

    try:
        caveaux = await get_caveaux_disponibles()
        is_mobile = page.width < 768

        if not caveaux:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_client(page, "caveaux"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Caveaux disponibles", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_caveaux_disponibles, page), bgcolor="#1976D2", color="white"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Text("Aucun caveau disponible", size=16, color=ft.Colors.GREY_600),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    ),
                ], expand=True, spacing=0)
            )
            page.update()
            return

        def on_reserver_click(e, caveau_id):
            # FIX : le caveau choisi est maintenant transmis au formulaire
            # de réservation via la session, au lieu d'être ignoré.
            session.set("selected_caveau_id", caveau_id)
            navigate_to(page, "create_reservation")

        items = []
        for c in caveaux:
            prix = c.get("prix_base", 0)
            prix_affichage = f"{prix:,.0f} FCFA" if prix > 0 else "Prix non défini"

            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c['reference'], size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(ft.Text("Disponible", size=12, color="white"), bgcolor=ft.Colors.GREEN, padding=5, border_radius=5),
                            ]),
                            ft.Text(f"Section: {c.get('section', 'N/A')} - Bloc: {c.get('bloc', 'N/A')}"),
                            ft.Text(f"Prix: {prix_affichage}", size=14, weight=ft.FontWeight.BOLD),
                            ft.Button("Réserver", on_click=lambda e, cid=c['id']: on_reserver_click(e, cid), bgcolor="#1976D2", color="white"),
                        ], spacing=5),
                        padding=10,
                    ),
                    elevation=2,
                )
            )

        grid = ft.GridView(
            controls=items,
            runs_count=1 if is_mobile else 2 if page.width < 1024 else 3,
            max_extent=350,
            spacing=10,
            run_spacing=10,
            child_aspect_ratio=1.2,
            padding=10,
        )

        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_client(page, "caveaux"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Caveaux disponibles", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_caveaux_disponibles, page), bgcolor="#1976D2", color="white"),
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
                get_header_client(page, "caveaux"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Réessayer", on_click=lambda e: page.run_task(load_caveaux_disponibles, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()