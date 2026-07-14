import flet as ft
from utils.api import get_users, change_user_role, toggle_user_active, logout
from utils.session import session


# HEADER ADMIN (reutilise)

def get_header_admin(page: ft.Page, active_item: str = ""):
    from pages.dashboard_admin import get_header_admin as header_admin
    return header_admin(page, active_item)


def navigate_to(page: ft.Page, destination: str):
    from pages.dashboard_admin import navigate_to as nav_to
    nav_to(page, destination)


# PAGE GESTION DES UTILISATEURS

def gestion_utilisateurs_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    if user.get("role") != "admin":
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)
        return
    
    page.title = "Gestion des utilisateurs"
    page.controls.clear()
    is_mobile = page.width < 768
    
    message_label = ft.Text("", size=14, color=ft.Colors.GREEN)
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        gestion_utilisateurs_page(page)
    page.on_resize = on_resize
    
    list_container = ft.Container(
        content=ft.Column([
            ft.Text("Liste des utilisateurs", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),
            message_label,
            ft.ProgressRing(),
            ft.Text("Chargement..."),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
        expand=True,
    )
    
    async def load_users():
        print("load_users: Debut chargement des utilisateurs")
        try:
            users = await get_users()
            print(f"load_users: Utilisateurs charges: {len(users) if users else 0}")
            
            if users and isinstance(users, list) and len(users) > 0:
                session.set("users_cache", users)
                list_container.content = build_users_list(users, is_mobile)
            else:
                list_container.content = build_empty_list()
            page.update()
        except Exception as e:
            print(f"load_users: Erreur: {e}")
            list_container.content = ft.Column([
                ft.Text("Liste des utilisateurs", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                message_label,
                ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            page.update()
    
    def build_empty_list():
        return ft.Column([
            ft.Text("Aucun utilisateur trouve", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Les utilisateurs apparaitront ici apres leur inscription", size=14, color=ft.Colors.GREY_600),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    
    def build_users_list(users, is_mobile):
        print(f"build_users_list: Construction de la liste, {len(users)} utilisateurs")
        
        if not users:
            return build_empty_list()
        
        current_user = session.get("user", {})
        current_username = current_user.get("username", "")
        
        items = []
        for u in users:
            is_current_admin = (u.get("username") == current_username and u.get("role") == "admin")
            
            role_colors = {
                "admin": ft.Colors.RED_700,
                "agent": ft.Colors.BLUE_700,
                "secretariat": ft.Colors.ORANGE_700,
                "client": ft.Colors.GREEN_700,
            }
            role_color = role_colors.get(u.get("role", "client"), ft.Colors.GREY_700)
            status_color = ft.Colors.GREEN if u.get("is_active") else ft.Colors.RED
            status_text = "Actif" if u.get("is_active") else "Inactif"
            
            # ✅ Fonction pour changer le role (avec uid et username en parametres)
            def on_role_change(role, uid, username):
                print(f"on_role_change: Changement role de {username} vers {role}")
                page.run_task(handle_change_role, page, uid, role, username)
            
            def on_toggle_active(e, uid=u['id'], username=u.get('username', '')):
                print(f"on_toggle_active: Changement statut de {username}")
                page.run_task(handle_toggle_active, page, uid, username)
            
            card_content = ft.Column([
                ft.Row([
                    ft.Text(u.get("username", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        ft.Text(u.get("role", "client"), size=11, color=ft.Colors.WHITE),
                        bgcolor=role_color,
                        padding=10,
                        border_radius=10,
                    ),
                    ft.Container(
                        ft.Text(status_text, size=11, color=ft.Colors.WHITE),
                        bgcolor=status_color,
                        padding=10,
                        border_radius=10,
                    ),
                ]),
                ft.Text(f"Email: {u.get('email', 'N/A')}", size=13),
                ft.Text(f"Telephone: {u.get('phone', 'N/A')}", size=13),
                ft.Text(f"Inscrit le: {u.get('date_joined', 'N/A')[:10] if u.get('date_joined') else 'N/A'}", size=12, color=ft.Colors.GREY_600),
                ft.Row([
                    ft.PopupMenuButton(
                        content=ft.Text("Rôle", size=12, 
                                       color=ft.Colors.GREY_400 if is_current_admin else ft.Colors.BLUE_700, 
                                       weight=ft.FontWeight.BOLD),
                        tooltip="Changer le role" if not is_current_admin else "Vous ne pouvez pas changer votre propre role",
                        disabled=is_current_admin,
                        items=[
                            # ✅ CORRECTION : uid et username figés comme defaults (evite le late binding sur u)
                            ft.PopupMenuItem(
                                content=ft.Text("Admin"),
                                on_click=lambda e, role="admin", uid=u['id'], uname=u.get('username', ''): on_role_change(role, uid, uname)
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Agent"),
                                on_click=lambda e, role="agent", uid=u['id'], uname=u.get('username', ''): on_role_change(role, uid, uname)
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Secretariat"),
                                on_click=lambda e, role="secretariat", uid=u['id'], uname=u.get('username', ''): on_role_change(role, uid, uname)
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Client"),
                                on_click=lambda e, role="client", uid=u['id'], uname=u.get('username', ''): on_role_change(role, uid, uname)
                            ),
                        ],
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("Actif" if u.get("is_active") else "Inactif"),
                        bgcolor=ft.Colors.GREY_400 if is_current_admin else (ft.Colors.GREEN if u.get("is_active") else ft.Colors.RED),
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(text_style=ft.TextStyle(size=11)),
                        on_click=None if is_current_admin else on_toggle_active,
                        disabled=is_current_admin,
                    ),
                ], spacing=10),
            ])
            
            if is_current_admin:
                items.append(
                    ft.Card(
                        content=ft.Container(
                            card_content,
                            padding=8,
                            width=400 if not is_mobile else page.width - 100,
                            bgcolor=ft.Colors.GREY_50,
                        ),
                        elevation=1,
                    )
                )
            else:
                items.append(
                    ft.Card(
                        content=ft.Container(
                            card_content,
                            padding=8,
                            width=400 if not is_mobile else page.width - 100,
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
    
    async def handle_change_role(page: ft.Page, user_id: int, role: str, username: str):
        print(f"handle_change_role: Debut - user_id={user_id}, role={role}, username={username}")
        try:
            current_user = session.get("user", {})
            
            # ✅ Bloque seulement si on essaie de changer son propre role
            if username == current_user.get("username"):
                print("handle_change_role: Tentative de changer son propre role")
                message_label.value = "Vous ne pouvez pas changer votre propre role !"
                message_label.color = ft.Colors.RED
                page.update()
                return
            
            print(f"handle_change_role: Appel API change_user_role({user_id}, {role})")
            result = await change_user_role(user_id, role)
            print(f"handle_change_role: Resultat: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message_label.value = f"Erreur: {result['error']}"
                    message_label.color = ft.Colors.RED
                    page.update()
                    return
                if "success" in result:
                    message_label.value = f"Role de {username} change en {role}"
                    message_label.color = ft.Colors.GREEN
                    page.update()
                    print(f"handle_change_role: Succes: role de {username} change en {role}")
            
            await load_users()
            
        except Exception as e:
            print(f"handle_change_role: Exception: {e}")
            message_label.value = f"Erreur: {e}"
            message_label.color = ft.Colors.RED
            page.update()
    
    async def handle_toggle_active(page: ft.Page, user_id: int, username: str):
        print(f"handle_toggle_active: Debut - user_id={user_id}, username={username}")
        try:
            current_user = session.get("user", {})
            if username == current_user.get("username"):
                print("handle_toggle_active: Tentative de se desactiver soi-meme")
                message_label.value = "Vous ne pouvez pas vous desactiver vous-meme !"
                message_label.color = ft.Colors.RED
                page.update()
                return
            
            print(f"handle_toggle_active: Appel API toggle_user_active({user_id})")
            result = await toggle_user_active(user_id)
            print(f"handle_toggle_active: Resultat: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message_label.value = f"Erreur: {result['error']}"
                    message_label.color = ft.Colors.RED
                    page.update()
                    return
                if "success" in result:
                    new_status = "active" if result.get("is_active", True) else "desactive"
                    message_label.value = f"Compte de {username} {new_status} avec succes"
                    message_label.color = ft.Colors.GREEN
                    page.update()
                    print(f"handle_toggle_active: Succes: compte de {username} {new_status}")
            
            await load_users()
            
        except Exception as e:
            print(f"handle_toggle_active: Exception: {e}")
            message_label.value = f"Erreur: {e}"
            message_label.color = ft.Colors.RED
            page.update()
    
    page.controls.append(
        ft.Column([
            get_header_admin(page, "users"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des utilisateurs", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_users), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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
    
    async def init():
        await load_users()
    
    page.run_task(init)