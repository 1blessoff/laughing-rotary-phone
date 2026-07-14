import flet as ft
from utils.session import session
from utils.api import put_request


def edit_profile_page(page: ft.Page):
    from pages.dashboard_client import get_header_client, refresh_current_page, client_dashboard

    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Mon profil"
    page.controls.clear()
    is_mobile = page.width < 768

    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    username = user.get("username", "")
    email = user.get("email", "")
    phone = user.get("phone", "")

    message = ft.Text("", color=ft.Colors.GREEN, size=14)

    def save_profile(e):
        new_username = username_field.value
        new_phone = phone_field.value
        new_password = password_field.value

        if not new_username:
            message.value = "Le nom d'utilisateur ne peut pas etre vide"
            message.color = ft.Colors.RED
            page.update()
            return

        data = {
            "username": new_username,
            "phone": new_phone,
        }

        if new_password:
            data["password"] = new_password

        page.run_task(handle_update_profile, page, data)

    async def handle_update_profile(page: ft.Page, data: dict):
        try:
            result = await put_request("auth/update-profile", data)
            print(f"Resultat mise a jour: {result}")

            if result and isinstance(result, dict):
                if "error" in result:
                    message.value = f"Erreur: {result['error']}"
                    message.color = ft.Colors.RED
                    page.update()
                    return

                if result.get("success"):
                    user = session.get("user", {})
                    user["username"] = data.get("username", user.get("username"))
                    user["phone"] = data.get("phone", user.get("phone"))
                    session.set("user", user)

                    message.value = "Profil mis a jour avec succes"
                    message.color = ft.Colors.GREEN
                    page.update()

        except Exception as e:
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()

    username_field = ft.TextField(
        label="Nom d'utilisateur",
        value=username,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.WHITE,
        border_color="#1A237E",
        focused_border_color="#1976D2",
    )

    email_field = ft.TextField(
        label="Email",
        value=email,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.GREY_200,
        border_color="#1A237E",
        read_only=True,
        disabled=True,
    )

    phone_field = ft.TextField(
        label="Telephone",
        value=phone,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.WHITE,
        border_color="#1A237E",
        focused_border_color="#1976D2",
    )

    password_field = ft.TextField(
        label="Nouveau mot de passe",
        password=True,
        can_reveal_password=True,
        width=page.width - 40 if is_mobile else 400,
        bgcolor=ft.Colors.WHITE,
        border_color="#1A237E",
        focused_border_color="#1976D2",
        hint_text="Laissez vide pour ne pas changer",
    )

    form = ft.Container(
        content=ft.Column([
            ft.Text("Informations personnelles", size=18, weight=ft.FontWeight.BOLD, color="#1A237E"),
            ft.Divider(height=10),
            username_field,
            email_field,
            phone_field,
            ft.Divider(height=15),
            ft.Text("Securite", size=18, weight=ft.FontWeight.BOLD, color="#1A237E"),
            ft.Divider(height=10),
            password_field,
            ft.Divider(height=15),
            message,
            ft.Row([
                ft.Button("Enregistrer", on_click=save_profile, bgcolor="#1976D2", color="white"),
                ft.Button("Retour", on_click=lambda e: client_dashboard(page), bgcolor=ft.Colors.GREY_400, color="white"),
            ], spacing=10),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        padding=25,
        bgcolor="#F5F7FA",
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
    )

    page.controls.append(
        ft.Column([
            get_header_client(page, "profile"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Mon profil", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=20),
                    form,
                ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
                bgcolor=ft.Colors.GREY_50,
            ),
        ], expand=True, spacing=0)
    )
    page.update()