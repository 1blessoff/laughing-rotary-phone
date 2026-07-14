from utils.api import put_request
import flet as ft
import os
import webbrowser
from utils.api import (
    get_caveaux,
    get_reservations_attente,
    get_concessions,
    valider_reservation,
    refuser_reservation,
    get_reservations,
    logout,
    get_caveaux_disponibles,
    changer_statut_caveau
)
from utils.session import session

# ============================================
# HEADER RESPONSIVE AGENT
# ============================================

def get_header_agent(page: ft.Page, active_item: str = ""):
    user = session.get("user", {})
    username = user.get("username", "Agent")
    role = "agent"
    
    def on_logout(e):
        page.run_task(handle_logout)
    
    async def handle_logout():
        await logout()
        session.clear()
        from pages.auth import login_page
        login_page(page)
    
    def on_edit_profile(e):
        edit_profile_page(page)
    
    is_mobile = page.width < 768
    
    menu_items = [
        ft.TextButton("Tableau de bord", on_click=lambda e: navigate_to(page, "dashboard"),
                      style=ft.ButtonStyle(color="white" if active_item!="dashboard" else "#4FC3F7")),
        ft.TextButton("Carte", on_click=lambda e: navigate_to(page, "map"),
                      style=ft.ButtonStyle(color="white" if active_item!="map" else "#4FC3F7")),
        ft.TextButton("Caveaux", on_click=lambda e: navigate_to(page, "caveaux"),
                      style=ft.ButtonStyle(color="white" if active_item!="caveaux" else "#4FC3F7")),
        ft.TextButton("Reservations", on_click=lambda e: navigate_to(page, "reservations"),
                      style=ft.ButtonStyle(color="white" if active_item!="reservations" else "#4FC3F7")),
        ft.TextButton("Concessions", on_click=lambda e: navigate_to(page, "concessions"),
                      style=ft.ButtonStyle(color="white" if active_item!="concessions" else "#4FC3F7")),
        ft.TextButton("Profil", on_click=on_edit_profile,
                      style=ft.ButtonStyle(color="white" if active_item!="profile" else "#4FC3F7")),
    ]
    
    if not is_mobile:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Espace Agent", size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row(menu_items, spacing=10),
                        ft.Row([
                            ft.Text(f"{username} ({role})", size=12, color="white"),
                            ft.TextButton("Deconnexion", on_click=on_logout, style=ft.ButtonStyle(color="white")),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#1976D2",
                ),
            ], spacing=0),
            width=page.width,
        )
    else:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Agent", size=18, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Row([
                            ft.Text(f"{username}", size=12, color="white"),
                            ft.PopupMenuButton(
                                icon=None,
                                content=ft.Text("Menu", color="white"),
                                items=[
                                    ft.PopupMenuItem(content=ft.Text("Tableau de bord"), on_click=lambda e: navigate_to(page, "dashboard")),
                                    ft.PopupMenuItem(content=ft.Text("Carte"), on_click=lambda e: navigate_to(page, "map")),
                                    ft.PopupMenuItem(content=ft.Text("Caveaux"), on_click=lambda e: navigate_to(page, "caveaux")),
                                    ft.PopupMenuItem(content=ft.Text("Reservations"), on_click=lambda e: navigate_to(page, "reservations")),
                                    ft.PopupMenuItem(content=ft.Text("Concessions"), on_click=lambda e: navigate_to(page, "concessions")),
                                    ft.PopupMenuItem(content=ft.Text("Profil"), on_click=lambda e: edit_profile_page(page)),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(content=ft.Text("Deconnexion"), on_click=on_logout),
                                ],
                            ),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#1976D2",
                ),
            ], spacing=0),
            width=page.width,
        )


def navigate_to(page: ft.Page, destination: str):
    if destination == "dashboard":
        agent_dashboard(page)
    elif destination == "map":
        page.run_task(ouvrir_carte_directe, page)
    elif destination == "caveaux":
        caveaux_page(page)
    elif destination == "reservations":
        reservations_page(page)
    elif destination == "concessions":
        concessions_page(page)
    elif destination == "profile":
        edit_profile_page(page)


def refresh_current_page(page: ft.Page):
    title = page.title
    if "Agent Dashboard" in title:
        agent_dashboard(page)
    elif "Caveaux" in title:
        caveaux_page(page)
    elif "Reservations" in title:
        reservations_page(page)
    elif "Concessions" in title:
        concessions_page(page)
    elif "Profil" in title:
        edit_profile_page(page)
    else:
        agent_dashboard(page)


# ============================================
# HTML DE LA CARTE (Agent)
# ============================================

def get_carte_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carte des caveaux</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            html, body { height: 100%; width: 100%; }
            #map { height: 100%; width: 100%; }
            .legend {
                position: absolute;
                bottom: 20px;
                left: 20px;
                background: rgba(255,255,255,0.95);
                padding: 12px 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                z-index: 1000;
                font-size: 13px;
                font-family: Arial, sans-serif;
            }
            .legend-item { display: flex; align-items: center; margin: 4px 0; }
            .legend-color { width: 16px; height: 16px; border-radius: 50%; margin-right: 10px; border: 1px solid rgba(0,0,0,0.2); }
            .popup-content { font-family: Arial, sans-serif; font-size: 13px; }
            .popup-content strong { color: #1a237e; }
            .popup-statut { display: inline-block; padding: 2px 8px; border-radius: 4px; color: white; font-size: 11px; font-weight: bold; margin-top: 3px; }
            .popup-statut.disponible { background: #4CAF50; }
            .popup-statut.reserve { background: #FF9800; }
            .popup-statut.occupe { background: #F44336; }
            .popup-statut.non_exploitable { background: #9E9E9E; }
            .btn-refresh {
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background: #1976D2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
                cursor: pointer;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            .btn-refresh:hover { background: #1565C0; }
        </style>
    </head>
    <body>
        <button class="btn-refresh" onclick="rafraichirCarte()">Rafraichir</button>
        <div id="map"></div>
        <div class="legend">
            <div class="legend-item"><div class="legend-color" style="background:#4CAF50;"></div> Disponible</div>
            <div class="legend-item"><div class="legend-color" style="background:#FF9800;"></div> Reserve</div>
            <div class="legend-item"><div class="legend-color" style="background:#F44336;"></div> Occupe</div>
            <div class="legend-item"><div class="legend-color" style="background:#9E9E9E;"></div> Non exploitable</div>
        </div>
        <script>
            var map = null;
            
            function initMap() {
                map = L.map('map').setView([-4.2634, 15.2429], 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19,
                }).addTo(map);
                chargerCaveaux();
            }
            
            function chargerCaveaux() {
                fetch('http://127.0.0.1:8000/api/caveaux/')
                .then(response => response.json())
                .then(data => {
                    if (map) {
                        map.eachLayer(function(layer) {
                            if (layer instanceof L.CircleMarker) {
                                map.removeLayer(layer);
                            }
                        });
                    }
                    
                    var bounds = [];
                    data.forEach(function(caveau) {
                        if (caveau.latitude && caveau.longitude) {
                            var color = '#4CAF50';
                            var statutClasse = 'disponible';
                            if (caveau.statut === 'reserve') { color = '#FF9800'; statutClasse = 'reserve'; }
                            else if (caveau.statut === 'occupe') { color = '#F44336'; statutClasse = 'occupe'; }
                            else if (caveau.statut === 'non_exploitable') { color = '#9E9E9E'; statutClasse = 'non_exploitable'; }
                            
                            var marker = L.circleMarker([caveau.latitude, caveau.longitude], {
                                radius: 12,
                                fillColor: color,
                                color: '#FFFFFF',
                                weight: 2,
                                opacity: 1,
                                fillOpacity: 0.9
                            }).addTo(map);
                            
                            var prix = caveau.prix_base || 0;
                            var prix_affichage = prix > 0 ? prix.toLocaleString() + ' FCFA' : 'Prix non defini';
                            
                            marker.bindPopup(
                                '<div class="popup-content">' +
                                '<strong>' + caveau.reference + '</strong><br>' +
                                'Statut: <span class="popup-statut ' + statutClasse + '">' + caveau.statut + '</span><br>' +
                                'Section: ' + caveau.section + '<br>' +
                                'Bloc: ' + (caveau.bloc || 'N/A') + '<br>' +
                                'Categorie: ' + (caveau.categorie_nom || 'N/A') + '<br>' +
                                'Prix: ' + prix_affichage +
                                '</div>',
                                { maxWidth: 300 }
                            );
                            bounds.push([caveau.latitude, caveau.longitude]);
                        }
                    });
                    if (bounds.length > 0) { map.fitBounds(bounds, { padding: [30, 30] }); }
                })
                .catch(function(error) { console.error('Erreur:', error); });
            }
            
            function rafraichirCarte() {
                chargerCaveaux();
            }
            
            window.onload = function() {
                initMap();
            };
        </script>
    </body>
    </html>
    """


async def ouvrir_carte_directe(page: ft.Page):
    try:
        html_content = get_carte_html()
        
        temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        html_path = os.path.join(temp_dir, "agent_map.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        url = f"file:///{html_path.replace(os.sep, '/')}"
        webbrowser.open(url)
        show_snackbar(page, "Carte ouverte - cliquez sur Rafraichir pour voir les changements", ft.Colors.GREEN)
        
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


def show_snackbar(page: ft.Page, message: str, color):
    page.snack_bar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=color,
        duration=3000,
        open=True,
    )
    page.update()


# ============================================
# DASHBOARD AGENT
# ============================================

def agent_dashboard(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Agent Dashboard"
    page.controls.clear()
    
    username = user.get("username", "Agent")
    
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    main_content = ft.Column([
        ft.Row([ft.Text("Tableau de bord Agent", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD)]),
        ft.Text(f"Bienvenue {username}", size=18 if not is_mobile else 16),
        ft.Divider(height=20),
        ft.ProgressRing(),
        ft.Text("Chargement des statistiques..."),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True, spacing=10)
    
    page.controls.append(
        ft.Column([
            get_header_agent(page, "dashboard"),
            ft.Container(
                content=main_content,
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_agent_stats, page)


async def load_agent_stats(page: ft.Page):
    try:
        caveaux = await get_caveaux()
        reservations = await get_reservations()
        reservations_attente = await get_reservations_attente()
        concessions = await get_concessions()
        
        total_caveaux = len(caveaux)
        disponibles = len([c for c in caveaux if c["statut"] == "disponible"])
        reserves = len([c for c in caveaux if c["statut"] == "reserve"])
        occupes = len([c for c in caveaux if c["statut"] == "occupe"])
        
        total_reservations = len(reservations)
        
        # ✅ CORRECTION : Vérifier le type de reservations_attente
        try:
            if isinstance(reservations_attente, dict):
                en_attente = reservations_attente.get("total", 0)
            else:
                en_attente = len(reservations_attente) if isinstance(reservations_attente, list) else 0
        except AttributeError:
            en_attente = 0
        
        validees = len([r for r in reservations if r["statut"] == "validee"])
        
        total_concessions = len(concessions)
        
        is_mobile = page.width < 768
        
        def create_stat_card(title, value, color=ft.Colors.GREY_700, value_size=28):
            return ft.Card(
                content=ft.Container(
                    ft.Column([
                        ft.Text(title, size=14 if not is_mobile else 12, color=color, text_align=ft.TextAlign.CENTER),
                        ft.Text(str(value), size=value_size if not is_mobile else 22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=15 if is_mobile else 20,
                    width=150 if not is_mobile else (page.width - 40) // 2 - 10,
                ),
                elevation=3,
            )
        
        def create_action_card(title, button_text, on_click, bgcolor="#1976D2"):
            return ft.Card(
                content=ft.Container(
                    ft.Column([
                        ft.Text(title, size=16 if not is_mobile else 14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=10),
                        ft.Button(button_text, on_click=on_click, bgcolor=bgcolor, color="white", width=160 if not is_mobile else page.width - 60),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, tight=True),
                    padding=15,
                    width=190 if not is_mobile else page.width - 20,
                ),
                elevation=3,
            )
        
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_agent(page, "dashboard"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Tableau de bord Agent", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=20),
                        
                        ft.Text("Caveaux", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_stat_card("Total", total_caveaux, ft.Colors.BLUE),
                            create_stat_card("Disponibles", disponibles, ft.Colors.GREEN),
                            create_stat_card("Reserves", reserves, ft.Colors.ORANGE),
                            create_stat_card("Occupes", occupes, ft.Colors.RED),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20),
                        
                        ft.Text("Reservations", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_stat_card("Total", total_reservations, ft.Colors.BLUE),
                            create_stat_card("En attente", en_attente, ft.Colors.ORANGE),
                            create_stat_card("Validees", validees, ft.Colors.GREEN),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20),
                        
                        ft.Text("Concessions", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_stat_card("Total", total_concessions, ft.Colors.BLUE),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20),
                        
                        ft.Text("Actions rapides", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_action_card("Carte", "Ouvrir", lambda e: navigate_to(page, "map"), "#79831C"),
                            create_action_card("Caveaux", "Gerer", lambda e: navigate_to(page, "caveaux"), "#1976D2"),
                            create_action_card("Reservations", "Gerer", lambda e: navigate_to(page, "reservations"), "#11695D"),
                            create_action_card("Concessions", "Voir", lambda e: navigate_to(page, "concessions"), "#9C27B0"),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=15),
                    expand=True,
                    padding=15 if is_mobile else 20,
                )
            ], expand=True, spacing=0)
        )
        page.update()
        
    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_agent(page, "dashboard"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Erreur de chargement", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(str(e), size=14),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_agent_stats, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    expand=True,
                    padding=20,
                )
            ], expand=True, spacing=0)
        )
        page.update()


# ============================================
# PAGES AGENT
# ============================================

async def changer_statut_caveau_action(page: ft.Page, caveau_id: int, statut_actuel: str):
    """Changer le statut d'un caveau en cycle"""
    from utils.api import changer_statut_caveau
    
    if statut_actuel == "disponible":
        nouveau_statut = "non_exploitable"
    elif statut_actuel == "non_exploitable":
        nouveau_statut = "disponible"
    else:
        nouveau_statut = "disponible"
    
    try:
        result = await changer_statut_caveau(caveau_id, nouveau_statut)
        if not result or "error" in result:
            erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
            show_snackbar(page, erreur, ft.Colors.RED)
            return
        show_snackbar(page, f"Statut modifie: {nouveau_statut}", ft.Colors.GREEN)
        await load_caveaux_list(page)
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


def caveaux_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Caveaux"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.controls.append(
        ft.Column([
            get_header_agent(page, "caveaux"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Gestion des caveaux", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
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
    page.run_task(load_caveaux_list, page)


async def load_caveaux_list(page: ft.Page):
    try:
        caveaux = await get_caveaux()
        is_mobile = page.width < 768
        
        if not caveaux:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_agent(page, "caveaux"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Gestion des caveaux", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_caveaux_list, page), bgcolor="#1976D2", color="white"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Text("Aucun caveau trouve", size=16, color=ft.Colors.GREY_600),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    ),
                ], expand=True, spacing=0)
            )
            page.update()
            return
        
        items = []
        for c in caveaux:
            color = ft.Colors.GREEN if c.get("statut") == "disponible" else ft.Colors.ORANGE if c.get("statut") == "reserve" else ft.Colors.RED
            prix = c.get("prix_base", 0)
            prix_affichage = f"{prix:,.0f} FCFA" if prix > 0 else "Prix non defini"
            
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c.get('reference', 'N/A'), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(c.get('statut', 'Inconnu'), size=12, color="white"),
                                    bgcolor=color,
                                    padding=5,
                                    border_radius=5,
                                ),
                            ]),
                            ft.Text(f"Section: {c.get('section', 'N/A')} - Bloc: {c.get('bloc', 'N/A')}", size=14),
                            ft.Text(f"Prix: {prix_affichage}", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Categorie: {c.get('categorie_nom', 'N/A')}", size=12, color=ft.Colors.GREY_600),
                            ft.Button(
                                "🔄 Changer statut",
                                on_click=lambda e, cid=c.get('id'), statut=c.get('statut'): page.run_task(changer_statut_caveau_action, page, cid, statut),
                                bgcolor="#FF9800",
                                color="white",
                                expand=is_mobile,
                            ),
                        ], spacing=5),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    ),
                    elevation=2,
                )
            )
        
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_agent(page, "caveaux"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Gestion des caveaux", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_caveaux_list, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Row(items, wrap=True, scroll=ft.ScrollMode.AUTO, spacing=15, run_spacing=15, height=500),
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
                get_header_agent(page, "caveaux"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_caveaux_list, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


def reservations_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Reservations"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.controls.append(
        ft.Column([
            get_header_agent(page, "reservations"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
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
    page.run_task(load_reservations_list, page)


async def load_reservations_list(page: ft.Page):
    try:
        data = await get_reservations_attente()
        is_mobile = page.width < 768
        
        # ✅ CORRECTION : Vérifier le type de data
        if isinstance(data, list):
            reservations = data
        elif isinstance(data, dict):
            reservations = data.get("reservations", [])
        else:
            reservations = []
        
        if not reservations:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_agent(page, "reservations"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_reservations_list, page), bgcolor="#1976D2", color="white"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Text("Aucune reservation en attente", size=16, color=ft.Colors.GREY_600),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    ),
                ], expand=True, spacing=0)
            )
            page.update()
            return
        
        items = []
        for r in reservations:
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(f"Reservation #{r.get('id', 'N/A')}", weight=ft.FontWeight.BOLD, size=16),
                                ft.Container(
                                    ft.Text("En attente", size=12, color="white"),
                                    bgcolor=ft.Colors.ORANGE,
                                    padding=5,
                                    border_radius=5,
                                ),
                            ]),
                            ft.Text(f"Defunt: {r.get('nom_defunt', 'N/A')}", size=14),
                            ft.Text(f"Caveau: {r.get('caveau_reference', 'N/A')}", size=14),
                            ft.Text(f"Client: {r.get('client_username', 'N/A')}", size=14),
                            ft.Row([
                                ft.Button("Valider", on_click=lambda e, rid=r.get('id'): page.run_task(valider_reservation_action, page, rid),
                                          bgcolor=ft.Colors.GREEN, color="white", expand=is_mobile),
                                ft.Button("Refuser", on_click=lambda e, rid=r.get('id'): page.run_task(refuser_reservation_action, page, rid),
                                          bgcolor=ft.Colors.RED, color="white", expand=is_mobile),
                            ], spacing=10),
                        ], spacing=5),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    ),
                    elevation=2,
                )
            )
        
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_agent(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_reservations_list, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Row(items, wrap=True, scroll=ft.ScrollMode.AUTO, spacing=15, run_spacing=15, height=500),
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
                get_header_agent(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_reservations_list, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()


async def valider_reservation_action(page: ft.Page, reservation_id: int):
    from utils.api import valider_reservation
    try:
        result = await valider_reservation(reservation_id)
        if not result or "error" in result:
            erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
            show_snackbar(page, erreur, ft.Colors.RED)
            return
        show_snackbar(page, f"Reservation #{reservation_id} validee", ft.Colors.GREEN)
        await load_reservations_list(page)
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


async def refuser_reservation_action(page: ft.Page, reservation_id: int):
    from utils.api import refuser_reservation
    try:
        result = await refuser_reservation(reservation_id, "Refuse par l'agent")
        if not result or "error" in result:
            erreur = result.get("error", "Erreur inconnue") if result else "Aucune reponse du serveur"
            show_snackbar(page, erreur, ft.Colors.RED)
            return
        show_snackbar(page, f"Reservation #{reservation_id} refusee", ft.Colors.RED)
        await load_reservations_list(page)
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


def concessions_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Concessions"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.controls.append(
        ft.Column([
            get_header_agent(page, "concessions"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_concessions_list, page), bgcolor="#1976D2", color="white"),
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
    page.run_task(load_concessions_list, page)


async def load_concessions_list(page: ft.Page):
    try:
        concessions = await get_concessions()
        is_mobile = page.width < 768
        
        if not concessions:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_agent(page, "concessions"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Gestion des concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_concessions_list, page), bgcolor="#1976D2", color="white"),
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
        for c in concessions:
            est_expiree = c.get("est_expiree", False)
            jours_restants = c.get("jours_restants")
            status_text = "Expiree" if est_expiree else f"{jours_restants} jours" if jours_restants else "Perpetuelle"
            status_color = ft.Colors.RED if est_expiree else ft.Colors.GREEN
            
            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(c.get("numero_contrat", "N/A"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(c.get("type_concession", "N/A"), size=11, color="white"),
                                    bgcolor=ft.Colors.BLUE_700,
                                    padding=5,
                                    border_radius=5,
                                ),
                                ft.Container(
                                    ft.Text(status_text, size=11, color="white"),
                                    bgcolor=status_color,
                                    padding=5,
                                    border_radius=5,
                                ),
                            ]),
                            ft.Text(f"Reservation: #{c.get('reservation_id', 'N/A')}"),
                            ft.Text(f"Debut: {c.get('date_debut', 'N/A')}"),
                            ft.Text(f"Fin: {c.get('date_fin', 'Perpetuelle')}"),
                        ], spacing=5),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    ),
                    elevation=2,
                )
            )
        
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_agent(page, "concessions"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Gestion des concessions", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                            ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_concessions_list, page), bgcolor="#1976D2", color="white"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Row(items, wrap=True, scroll=ft.ScrollMode.AUTO, spacing=15, run_spacing=15, height=500),
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
                get_header_agent(page, "concessions"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_concessions_list, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                ),
            ], expand=True, spacing=0)
        )
        page.update()



def edit_profile_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return

    page.title = "Profil"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        refresh_current_page(page)
    page.on_resize = on_resize

    user = session.get("user", {})
    username = user.get("username", "")
    email = user.get("email", "")
    phone = user.get("phone", "")

    message_label = ft.Text("", size=14, color=ft.Colors.GREEN)

    def save_profile(e):
        if not session.get("user"):
            message_label.value = " Veuillez vous reconnecter"
            message_label.color = ft.Colors.RED
            page.update()
            return
        
        data = {
            "username": username_field.value,
            "phone": phone_field.value,
            "password": password_field.value or "",
        }
        
        print(f" Données envoyées: {data}")
        page.run_task(handle_update_profile, page, data)

    async def handle_update_profile(page: ft.Page, data: dict):
        try:
            print(f"handle_update_profile: {data}")
            result = await put_request("auth/update-profile", data)
            print(f"Réponse: {result}")
            
            if result and isinstance(result, dict):
                if "error" in result:
                    message_label.value = f" {result['error']}"
                    message_label.color = ft.Colors.RED
                    page.update()
                    return
                if result.get("success"):
                    user = session.get("user", {})
                    user["username"] = data.get("username", user.get("username"))
                    user["phone"] = data.get("phone", user.get("phone"))
                    session.set("user", user)
                    message_label.value = "Profil mis a jour avec succes"
                    message_label.color = ft.Colors.GREEN
                    page.update()
                    return
            
            message_label.value = "Erreur lors de la mise a jour"
            message_label.color = ft.Colors.RED
            page.update()
            
        except Exception as e:
            print(f"Exception: {e}")
            message_label.value = f"Erreur: {e}"
            message_label.color = ft.Colors.RED
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
            message_label,
            ft.Row([
                ft.Button("Enregistrer", on_click=save_profile, bgcolor="#1976D2", color="white"),
                ft.Button("Retour", on_click=lambda e: agent_dashboard(page), bgcolor=ft.Colors.GREY_400, color="white"),
            ], spacing=10),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        padding=25,
        bgcolor="#E7EAEE",
        border_radius=10,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
    )

    page.controls.append(
        ft.Column([
            get_header_agent(page, "profile"),
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


def login_page(page: ft.Page):
    from pages.auth import login_page as auth_login
    auth_login(page)