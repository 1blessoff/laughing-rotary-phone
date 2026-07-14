

import flet as ft
from utils.session import session
from utils.api import login, register, verify_mfa, request_password_reset, confirm_password_reset, get_current_user

# ============================================
# CONSTANTES DE STYLE
# ============================================

COLOR_PRIMARY = "#1976D2"
COLOR_PRIMARY_DARK = "#1565C0"
COLOR_BG = "#F5F7FA"
COLOR_CARD = "#FFFFFF"

# ============================================
# FONCTIONS DE VALIDATION
# ============================================

def est_email_valide(email: str) -> bool:
    domaines_autorises = ("@gmail.com", "@yahoo.fr")
    return email.endswith(domaines_autorises)

def est_mot_de_passe_valide(password: str) -> tuple:
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caracteres"
    if len(password) > 16:
        return False, "Le mot de passe ne doit pas depasser 16 caracteres"
    return True, ""

def est_champ_rempli(champ: str) -> bool:
    return champ is not None and champ.strip() != ""

# ============================================
# REDIRECTION PAR ROLE
# ============================================

def redirect_by_role(page: ft.Page):
    """Redirige vers le dashboard correspondant au rôle"""
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    role = user.get("role", "client")
    print(f"=== redirect_by_role: role={role} ===")
    
    if role == "admin":
        from pages.dashboard_admin import admin_dashboard
        admin_dashboard(page)
    elif role == "agent":
        from pages.dashboard_agent import agent_dashboard
        agent_dashboard(page)
    elif role == "secretariat":
        from pages.dashboard_secretariat import secretariat_dashboard
        secretariat_dashboard(page)
    else:
        from pages.dashboard_client import client_dashboard
        client_dashboard(page)

# ============================================
# COMPOSANTS REUTILISABLES
# ============================================

def get_auth_header(page: ft.Page, title: str):
    """Header simplifié pour les pages d'authentification"""
    is_mobile = page.width < 768
    return ft.Container(
        content=ft.Row([
            ft.Text("Gestion Funéraire", size=20 if not is_mobile else 18, 
                    weight=ft.FontWeight.BOLD, color="white"),
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=15,
        bgcolor=COLOR_PRIMARY,
        width=page.width,
    )

def get_auth_container(page: ft.Page, content):
    """Container principal pour les pages d'authentification"""
    is_mobile = page.width < 768
    return ft.Container(
        content=ft.Column([
            get_auth_header(page, ""),
            ft.Container(
                content=content,
                expand=True,
                padding=20 if not is_mobile else 15,
                bgcolor=COLOR_BG,
            ),
        ], spacing=0, expand=True),
        expand=True,
    )

def get_auth_card(page: ft.Page, children):
    """Carte blanche pour les formulaires d'authentification"""
    is_mobile = page.width < 768
    return ft.Container(
        content=ft.Column(children, spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=30 if not is_mobile else 20,
        bgcolor=COLOR_CARD,
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.GREY_300, offset=ft.Offset(0, 4)),
        width=450 if not is_mobile else page.width - 30,
    )

def get_auth_field(label: str, password: bool = False, width: int = None, hint: str = None, 
                    max_length: int = None, input_filter: ft.InputFilter = None):
    """Champ de formulaire uniforme"""
    return ft.TextField(
        label=label,
        password=password,
        width=width,
        hint_text=hint,
        max_length=max_length,
        input_filter=input_filter,
        bgcolor=ft.Colors.WHITE,
        border_color=COLOR_PRIMARY,
        focused_border_color=COLOR_PRIMARY,
        focused_color=COLOR_PRIMARY,
        cursor_color=COLOR_PRIMARY,
    )

def get_auth_button(text: str, on_click, width: int = None, bgcolor: str = COLOR_PRIMARY):
    """Bouton uniforme"""
    return ft.Button(
        text,
        on_click=on_click,
        bgcolor=bgcolor,
        color="white",
        width=width,
        height=45,
    )

def get_auth_message(message: str, color: str = ft.Colors.RED):
    """Message d'erreur ou de succès uniforme"""
    return ft.Text(message, color=color, size=14, text_align=ft.TextAlign.CENTER)

# ============================================
# PAGE DE CONNEXION
# ============================================

def login_page(page: ft.Page):
    print("=== login_page: DEBUT ===")
    page.title = "Connexion"
    page.controls.clear()
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    
    is_mobile = page.width < 768
    field_width = 350 if not is_mobile else page.width - 60
    
    username = get_auth_field("Nom d'utilisateur", width=field_width)
    password = get_auth_field("Mot de passe", password=True, width=field_width)
    message = ft.Text("", color=ft.Colors.RED, size=14, text_align=ft.TextAlign.CENTER)
    
    def on_login(e):
        print("=== on_login: CLIC ===")
        if not est_champ_rempli(username.value):
            message.value = "Veuillez saisir votre nom d'utilisateur"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_champ_rempli(password.value):
            message.value = "Veuillez saisir votre mot de passe"
            message.color = ft.Colors.RED
            page.update()
            return
        
        print(f"=== on_login: username={username.value}, password=*** ===")
        page.run_task(handle_login, username.value, password.value)
    
    async def handle_login(username_val: str, password_val: str):
        print(f"=== handle_login: DEBUT pour {username_val} ===")
        try:
            data = await login(username_val, password_val)
            print(f"=== handle_login: data recue = {data} ===")
            
            if "error" in data:
                message.value = data["error"]
                message.color = ft.Colors.RED
                page.update()
                print(f"=== handle_login: ERREUR = {data['error']} ===")
                return
            
            if data.get("requires_mfa"):
                user_id = data["user"]["id"]
                print(f"=== handle_login: MFA requis, user_id={user_id} ===")
                session.set("mfa_user_id", user_id)
                session.set("mfa_username", data["user"]["username"])
                session.set("mfa_role", data["user"]["role"])
                page.controls.clear()
                page.update()
                print("=== handle_login: appel de mfa_page ===")
                mfa_page(page)
                print("=== handle_login: mfa_page terminee ===")
            else:
                print("=== handle_login: Connexion directe sans MFA ===")
                session.set("user", data["user"])
                redirect_by_role(page)
                
        except Exception as e:
            print(f"=== handle_login: EXCEPTION = {e} ===")
            message.value = f"Erreur de connexion: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    # Contenu principal
    content = ft.Column([
        ft.Text("Connexion", size=28 if not is_mobile else 24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_DARK),
        ft.Divider(height=10, color=ft.Colors.GREY_300),
        ft.Text("Connectez-vous à votre espace", size=14, color=ft.Colors.GREY_600),
        ft.Divider(height=10),
        get_auth_card(page, [
            username,
            password,
            message,
            get_auth_button("Se connecter", on_login, width=field_width),
            ft.Row([
                ft.TextButton("Mot de passe oublié", on_click=lambda e: forgot_password_page(page), 
                              style=ft.ButtonStyle(color=COLOR_PRIMARY)),
                ft.Text("|", size=14, color=ft.Colors.GREY_400),
                ft.TextButton("Créer un compte", on_click=lambda e: register_page(page),
                              style=ft.ButtonStyle(color=COLOR_PRIMARY)),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
        ]),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    
    page.controls.append(get_auth_container(page, content))
    page.update()
    print("=== login_page: FIN ===")


# ============================================
# PAGE MFA
# ============================================

def mfa_page(page: ft.Page):
    print("=== mfa_page: DEBUT ===")
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    
    user_id = session.get("mfa_user_id")
    username = session.get("mfa_username")
    mfa_role = session.get("mfa_role", "client")
    
    if not user_id:
        print("=== mfa_page: AUCUN ID TROUVE ===")
        page.controls.clear()
        content = ft.Column([
            ft.Text("Session expirée. Veuillez vous reconnecter.", size=18, color=ft.Colors.RED),
            get_auth_button("Retour à la connexion", lambda e: login_page(page), width=200),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
        page.controls.append(get_auth_container(page, content))
        page.update()
        return
    
    page.controls.clear()
    print(f"=== mfa_page: user_id={user_id}, username={username}, role={mfa_role} ===")
    
    is_mobile = page.width < 768
    field_width = 350 if not is_mobile else page.width - 60
    
    code = ft.TextField(
        label="Code MFA (6 chiffres)",
        width=field_width,
        max_length=6,
        input_filter=ft.NumbersOnlyInputFilter(),
        bgcolor=ft.Colors.WHITE,
        border_color=COLOR_PRIMARY,
        focused_border_color=COLOR_PRIMARY,
        focused_color=COLOR_PRIMARY,
        cursor_color=COLOR_PRIMARY,
    )
    message = ft.Text("", color=ft.Colors.RED, size=14, text_align=ft.TextAlign.CENTER)
    
    def on_verify(e):
        print("=== on_verify: CLIC ===")
        if not est_champ_rempli(code.value):
            message.value = "Veuillez saisir le code MFA"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if len(code.value) != 6:
            message.value = "Le code MFA doit contenir 6 chiffres"
            message.color = ft.Colors.RED
            page.update()
            return
        
        print(f"=== on_verify: code = {code.value} ===")
        page.run_task(handle_verify, code.value)
    
    async def handle_verify(code_val: str):
        print(f"=== handle_verify: DEBUT avec code={code_val} ===")
        try:
            user_id = session.get("mfa_user_id")
            mfa_role = session.get("mfa_role", "client")
            
            if not user_id:
                message.value = "Session expirée. Veuillez vous reconnecter."
                message.color = ft.Colors.RED
                page.update()
                return
            # Vérifier le code MFA et s'assurer que la session serveur est active
            data = await verify_mfa(code_val, user_id)
            print(f"=== handle_verify: data = {data} ===")

            if "error" in data:
                message.value = data["error"]
                message.color = ft.Colors.RED
                page.update()
                return

            # Demander /auth/me pour confirmer que le cookie de session a bien
            # été émis et que l'utilisateur est authentifié côté serveur.
            me = await get_current_user()
            print(f"=== handle_verify: get_current_user response = {me} ===")
            if not me or "error" in me:
                message.value = "Impossible de valider la session serveur. Veuillez vous reconnecter."
                message.color = ft.Colors.RED
                page.update()
                return

            # Utiliser la réponse serveur pour la session client
            session.remove("mfa_user_id")
            session.remove("mfa_username")
            session.remove("mfa_role")
            session.set("user", {
                "id": me.get("id"),
                "username": me.get("username"),
                "email": me.get("email"),
                "role": me.get("role"),
            })
            redirect_by_role(page)
            
        except Exception as e:
            print(f"=== handle_verify: EXCEPTION = {e} ===")
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    content = ft.Column([
        ft.Text("Vérification MFA", size=28 if not is_mobile else 24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_DARK),
        ft.Divider(height=10, color=ft.Colors.GREY_300),
        ft.Text("Un code a été envoyé à votre email.", size=14, color=ft.Colors.GREY_600),
        ft.Text(f"Connecté en tant que: {username}", size=14, color=COLOR_PRIMARY),
        ft.Divider(height=10),
        get_auth_card(page, [
            code,
            message,
            get_auth_button("Vérifier", on_verify, width=field_width),
            ft.TextButton("Retour à la connexion", on_click=lambda e: login_page(page),
                          style=ft.ButtonStyle(color=COLOR_PRIMARY)),
        ]),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    
    page.controls.append(get_auth_container(page, content))
    page.update()
    print("=== mfa_page: FIN ===")


# ============================================
# PAGE D'INSCRIPTION
# ============================================

def register_page(page: ft.Page):
    print("=== register_page: DEBUT ===")
    page.title = "Inscription"
    page.controls.clear()
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    
    is_mobile = page.width < 768
    field_width = 350 if not is_mobile else page.width - 60
    
    username = get_auth_field("Nom d'utilisateur", width=field_width)
    email = get_auth_field("Email", width=field_width)
    phone = get_auth_field("Téléphone", width=field_width)
    password = get_auth_field("Mot de passe (8-16 caractères)", password=True, width=field_width)
    password2 = get_auth_field("Confirmer le mot de passe", password=True, width=field_width)
    message = ft.Text("", color=ft.Colors.RED, size=14, text_align=ft.TextAlign.CENTER)
    
    def on_register(e):
        print("=== on_register: CLIC ===")
        if not est_champ_rempli(username.value):
            message.value = "Veuillez saisir un nom d'utilisateur"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_champ_rempli(email.value):
            message.value = "Veuillez saisir votre email"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_champ_rempli(password.value):
            message.value = "Veuillez saisir un mot de passe"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_champ_rempli(password2.value):
            message.value = "Veuillez confirmer votre mot de passe"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_email_valide(email.value):
            message.value = "Veuillez saisir un email valide (@gmail.com ou @yahoo.fr)"
            message.color = ft.Colors.RED
            page.update()
            return
        
        est_valide, erreur = est_mot_de_passe_valide(password.value)
        if not est_valide:
            message.value = erreur
            message.color = ft.Colors.RED
            page.update()
            return
        
        if password.value != password2.value:
            message.value = "Les mots de passe ne correspondent pas"
            message.color = ft.Colors.RED
            page.update()
            return
        
        page.run_task(handle_register)
    
    async def handle_register():
        print("=== handle_register: DEBUT ===")
        try:
            data = await register({
                "username": username.value,
                "email": email.value,
                "phone": phone.value,
                "password": password.value,
                "password2": password2.value,
                "role": "client"
            })
            
            if "error" in data:
                message.value = data["error"]
                message.color = ft.Colors.RED
                page.update()
                return
            
            message.value = "Inscription réussie ! Vous pouvez vous connecter."
            message.color = ft.Colors.GREEN
            page.update()
            
            import time
            time.sleep(2)
            login_page(page)
            
        except Exception as e:
            print(f"=== handle_register: EXCEPTION = {e} ===")
            message.value = f"Erreur d'inscription: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    content = ft.Column([
        ft.Text("Inscription", size=28 if not is_mobile else 24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_DARK),
        ft.Divider(height=10, color=ft.Colors.GREY_300),
        ft.Text("Créez votre compte client", size=14, color=ft.Colors.GREY_600),
        ft.Divider(height=10),
        get_auth_card(page, [
            username,
            email,
            phone,
            password,
            password2,
            message,
            get_auth_button("S'inscrire", on_register, width=field_width),
            ft.TextButton("Déjà un compte ? Se connecter", on_click=lambda e: login_page(page),
                          style=ft.ButtonStyle(color=COLOR_PRIMARY)),
        ]),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    
    page.controls.append(get_auth_container(page, content))
    page.update()
    print("=== register_page: FIN ===")


# ============================================
# PAGE MOT DE PASSE OUBLIE
# ============================================

def forgot_password_page(page: ft.Page):
    print("=== forgot_password_page: DEBUT ===")
    page.title = "Mot de passe oublié"
    page.controls.clear()
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    
    is_mobile = page.width < 768
    field_width = 350 if not is_mobile else page.width - 60
    
    email = get_auth_field("Email", width=field_width)
    message = ft.Text("", color=ft.Colors.RED, size=14, text_align=ft.TextAlign.CENTER)
    
    def on_request(e):
        print("=== on_request: CLIC ===")
        if not est_champ_rempli(email.value):
            message.value = "Veuillez saisir votre email"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_email_valide(email.value):
            message.value = "Veuillez saisir un email valide (@gmail.com ou @yahoo.fr)"
            message.color = ft.Colors.RED
            page.update()
            return
        
        page.run_task(handle_request, email.value)
    
    async def handle_request(email_val: str):
        print(f"=== handle_request: DEBUT pour {email_val} ===")
        try:
            data = await request_password_reset(email_val)
            
            if "error" in data:
                message.value = data["error"]
                message.color = ft.Colors.RED
                page.update()
                return
            
            message.value = "Un code de réinitialisation a été envoyé par email."
            message.color = ft.Colors.GREEN
            page.update()
            
            reset_confirm_page(page, email_val)
            
        except Exception as e:
            print(f"=== handle_request: EXCEPTION = {e} ===")
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    content = ft.Column([
        ft.Text("Mot de passe oublié", size=28 if not is_mobile else 24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_DARK),
        ft.Divider(height=10, color=ft.Colors.GREY_300),
        ft.Text("Entrez votre email pour recevoir un code de réinitialisation.", size=14, color=ft.Colors.GREY_600),
        ft.Divider(height=10),
        get_auth_card(page, [
            email,
            message,
            get_auth_button("Envoyer le code", on_request, width=field_width),
            ft.TextButton("Retour à la connexion", on_click=lambda e: login_page(page),
                          style=ft.ButtonStyle(color=COLOR_PRIMARY)),
        ]),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    
    page.controls.append(get_auth_container(page, content))
    page.update()
    print("=== forgot_password_page: FIN ===")


# ============================================
# PAGE CONFIRMATION MOT DE PASSE OUBLIE
# ============================================

def reset_confirm_page(page: ft.Page, email_val: str):
    print(f"=== reset_confirm_page: DEBUT pour {email_val} ===")
    page.title = "Confirmation réinitialisation"
    page.controls.clear()
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    
    is_mobile = page.width < 768
    field_width = 350 if not is_mobile else page.width - 60
    
    code = ft.TextField(
        label="Code de réinitialisation",
        width=field_width,
        bgcolor=ft.Colors.WHITE,
        border_color=COLOR_PRIMARY,
        focused_border_color=COLOR_PRIMARY,
        focused_color=COLOR_PRIMARY,
        cursor_color=COLOR_PRIMARY,
    )
    new_password = get_auth_field("Nouveau mot de passe (8-16 caractères)", password=True, width=field_width)
    new_password2 = get_auth_field("Confirmer le mot de passe", password=True, width=field_width)
    message = ft.Text("", color=ft.Colors.RED, size=14, text_align=ft.TextAlign.CENTER)
    
    def on_confirm(e):
        print("=== on_confirm: CLIC ===")
        if not est_champ_rempli(code.value):
            message.value = "Veuillez saisir le code de réinitialisation"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_champ_rempli(new_password.value):
            message.value = "Veuillez saisir un nouveau mot de passe"
            message.color = ft.Colors.RED
            page.update()
            return
        
        if not est_champ_rempli(new_password2.value):
            message.value = "Veuillez confirmer le mot de passe"
            message.color = ft.Colors.RED
            page.update()
            return
        
        est_valide, erreur = est_mot_de_passe_valide(new_password.value)
        if not est_valide:
            message.value = erreur
            message.color = ft.Colors.RED
            page.update()
            return
        
        if new_password.value != new_password2.value:
            message.value = "Les mots de passe ne correspondent pas"
            message.color = ft.Colors.RED
            page.update()
            return
        
        page.run_task(handle_confirm)
    
    async def handle_confirm():
        print("=== handle_confirm: DEBUT ===")
        try:
            data = await confirm_password_reset(email_val, code.value, new_password.value)
            
            if "error" in data:
                message.value = data["error"]
                message.color = ft.Colors.RED
                page.update()
                return
            
            message.value = "Mot de passe réinitialisé avec succès."
            message.color = ft.Colors.GREEN
            page.update()
            
            import time
            time.sleep(2)
            login_page(page)
            
        except Exception as e:
            print(f"=== handle_confirm: EXCEPTION = {e} ===")
            message.value = f"Erreur: {e}"
            message.color = ft.Colors.RED
            page.update()
    
    content = ft.Column([
        ft.Text("Confirmation", size=28 if not is_mobile else 24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_DARK),
        ft.Divider(height=10, color=ft.Colors.GREY_300),
        ft.Text(f"Un code a été envoyé à {email_val}", size=14, color=ft.Colors.GREY_600),
        ft.Divider(height=10),
        get_auth_card(page, [
            code,
            new_password,
            new_password2,
            message,
            get_auth_button("Réinitialiser", on_confirm, width=field_width),
            ft.TextButton("Retour à la connexion", on_click=lambda e: login_page(page),
                          style=ft.ButtonStyle(color=COLOR_PRIMARY)),
        ]),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    
    page.controls.append(get_auth_container(page, content))
    page.update()
    print("=== reset_confirm_page: FIN ===")