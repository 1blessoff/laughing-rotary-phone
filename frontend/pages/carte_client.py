import flet as ft
from utils.session import session

# Adaptez si votre backend n'est pas en local sur ce port.
from utils.api import API_URL

# Deduite de API_URL ("http://127.0.0.1:8000/api" -> "http://127.0.0.1:8000")
# pour n'avoir qu'un seul endroit a changer lors du deploiement.
CARTE_URL = f"{API_URL.rsplit('/api', 1)[0]}/carte-caveaux/"


def _webview_supporte(page: ft.Page) -> bool:
    """
    ft.WebView (flet_webview) ne fonctionne que sur iOS, Android, macOS et Web.
    Il n'est PAS supporté sur Windows/Linux desktop (limitation de Flet, pas
    un bug de notre côté). On détecte la plateforme pour proposer un
    fallback propre plutôt qu'un écran vide ou une erreur silencieuse.
    """
    if getattr(page, "web", False):
        return True
    platform = getattr(page, "platform", None)
    if platform is None:
        return False
    plateformes_supportees = {"macos", "ios", "android"}
    return str(platform).lower().split(".")[-1] in plateformes_supportees


def carte_client_page(page: ft.Page):
    from pages.dashboard_client import get_header_client, refresh_current_page

    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Carte des caveaux"
    page.controls.clear()
    is_mobile = page.width < 768

    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    if _webview_supporte(page):
        try:
            import flet_webview as fwv
            carte_content = fwv.WebView(
                url=CARTE_URL,
                expand=True,
                on_web_resource_error=lambda e: print("Erreur carte:", e.data),
            )
        except Exception as e:
            carte_content = _fallback_ouverture_externe(page, str(e))
    else:
        carte_content = _fallback_ouverture_externe(page)

    page.controls.append(
        ft.Column([
            get_header_client(page, "carte"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Carte des caveaux", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    ft.Container(content=carte_content, expand=True, border_radius=10),
                ], expand=True),
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()


def _fallback_ouverture_externe(page: ft.Page, erreur: str = None):
    """
    Sur Windows/Linux desktop, ft.WebView n'est pas disponible : on ouvre la
    carte (même URL, avec auto-rafraîchissement toutes les 5s) dans le
    navigateur par défaut, comme le fait déjà le dashboard admin.
    """
    import webbrowser

    def ouvrir(e):
        webbrowser.open(CARTE_URL)

    message = (
        "L'affichage intégré de la carte n'est pas disponible sur l interface flet"
        "(cela  ne fonctionne que sur Web, iOS, Android et macOS)."
        "(Vous pouvez ouvrir la carte dans votre navigateur)"
    )
    if erreur:
        message += f"\n\nDétail : {erreur}"

    return ft.Column(
        [
            ft.Icon(ft.Icons.MAP_OUTLINED, size=64, color=ft.Colors.GREY_400),
            ft.Text(message, size=14, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
            ft.Button("Ouvrir la carte (mise à jour auto)", on_click=ouvrir, bgcolor="#1976D2", color="white"),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=15,
        expand=True,
    )