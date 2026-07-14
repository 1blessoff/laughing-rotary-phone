import flet as ft
from utils.api import get_concessions, get_reservations
from utils.session import session


def mes_concessions_page(page: ft.Page):
    from pages.dashboard_client import get_header_client, refresh_current_page

    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Mes concessions"
    page.controls.clear()
    is_mobile = page.width < 768

    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    page.controls.append(
        ft.Column([
            get_header_client(page, "concessions"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Mes concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_mes_concessions, page), bgcolor="#1976D2", color="white"),
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
    page.run_task(load_mes_concessions, page)


async def load_mes_concessions(page: ft.Page):
    from pages.dashboard_client import get_header_client

    try:
        concessions = await get_concessions()
        is_mobile = page.width < 768

        user = session.get("user", {})
        reservations = await get_reservations()
        user_reservation_ids = [r["id"] for r in reservations if r["client_id"] == user.get("id")]
        user_concessions = [c for c in concessions if c.get("reservation_id") in user_reservation_ids]

        if not user_concessions:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_client(page, "concessions"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Mes concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_mes_concessions, page), bgcolor="#1976D2", color="white"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Text("Aucune concession", size=16, color=ft.Colors.GREY_600),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    ),
                ], expand=True, spacing=0)
            )
            page.update()
            return

        items = []
        for c in user_concessions:
            est_expiree = c.get("est_expiree", False)
            jours_restants = c.get("jours_restants")

            status_color = ft.Colors.RED if est_expiree else ft.Colors.GREEN
            status_text = "Expirée" if est_expiree else f"{jours_restants} jours" if jours_restants else "Perpétuelle"

            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c.get("numero_contrat", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(ft.Text(c.get("type_concession", "N/A"), size=11, color="white"), bgcolor=ft.Colors.BLUE_700, padding=5, border_radius=5),
                                ft.Container(ft.Text(status_text, size=11, color="white"), bgcolor=status_color, padding=5, border_radius=5),
                            ]),
                            ft.Text(f"Début: {c.get('date_debut', 'N/A')}"),
                            ft.Text(f"Fin: {c.get('date_fin', 'Perpétuelle')}"),
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
                get_header_client(page, "concessions"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Mes concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraîchir", on_click=lambda e: page.run_task(load_mes_concessions, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Container(content=grid, expand=True, height=400),
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
                get_header_client(page, "concessions"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Réessayer", on_click=lambda e: page.run_task(load_mes_concessions, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()