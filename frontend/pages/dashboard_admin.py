import flet as ft
import os
from pages.gestion_concessions import gestion_concessions_page
from pages.gestion_exhumations import gestion_exhumations_page
from pages.gestion_paiements import gestion_paiements_page
import webbrowser
import subprocess
import time
from utils.api import (
    get_caveaux,
    get_paiements_stats,
    get_reservations_attente,
    get_reservations,
    get_concessions,
    get_exhumations,
    get_users,
    get_reservation,
    logout,
    valider_reservation,
    refuser_reservation,
    create_concession,
    renouveler_concession,
    create_paiement,
    valider_paiement,
    approuver_exhumation,
    refuser_exhumation,
    change_user_role,
    toggle_user_active,
)
from utils.session import session

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
# HTML DE LA CARTE (avec fonction de rafraîchissement)
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
        <button class="btn-refresh" onclick="rafraichirCarte()">Rafraîchir la page</button>
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
                    // Supprimer tous les marqueurs sauf les tuiles
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
                            var prix_affichage = prix > 0 ? prix.toLocaleString() + ' FCFA' : 'Prix non défini';
                            
                            marker.bindPopup(
                                '<div class="popup-content">' +
                                '<strong>' + caveau.reference + '</strong><br>' +
                                'Statut: <span class="popup-statut ' + statutClasse + '">' + caveau.statut + '</span><br>' +
                                'Section: ' + caveau.section + '<br>' +
                                'Bloc: ' + (caveau.bloc || 'N/A') + '<br>' +
                                'Catégorie: ' + (caveau.categorie_nom || 'N/A') + '<br>' +
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


# ============================================
# HEADER ADMIN
# ============================================

def get_header_admin(page: ft.Page, active_item: str = ""):
    user = session.get("user", {})
    username = user.get("username", "Admin")
    role = "admin"
    
    def on_logout(e):
        fermer_carte()
        page.run_task(handle_logout)
    
    def fermer_carte():
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], capture_output=True)
                subprocess.run(['taskkill', '/f', '/im', 'firefox.exe'], capture_output=True)
                subprocess.run(['taskkill', '/f', '/im', 'edge.exe'], capture_output=True)
            else:
                subprocess.run(['pkill', 'chrome'], capture_output=True)
                subprocess.run(['pkill', 'firefox'], capture_output=True)
        except:
            pass
    
    async def handle_logout():
        await logout()
        session.clear()
        from pages.auth import login_page
        login_page(page)
    
    is_mobile = page.width < 768
    
    menu_items = [
        ft.TextButton("Dashboard", on_click=lambda e: navigate_to(page, "dashboard"),
                      style=ft.ButtonStyle(color="white" if active_item!="dashboard" else "#4FC3F7")),
        ft.TextButton("Carte", on_click=lambda e: navigate_to(page, "map"),
                      style=ft.ButtonStyle(color="white" if active_item!="map" else "#4FC3F7")),
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
        ft.TextButton("Audit Logs", on_click=lambda e: navigate_to(page, "audits"),
                      style=ft.ButtonStyle(color="white" if active_item!="audits" else "#4FC3F7")),
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
                                    ft.PopupMenuItem(content=ft.Text("Carte"), on_click=lambda e: navigate_to(page, "map")),
                                    ft.PopupMenuItem(content=ft.Text("Caveaux"), on_click=lambda e: navigate_to(page, "caveaux")),
                                    ft.PopupMenuItem(content=ft.Text("Reservations"), on_click=lambda e: navigate_to(page, "reservations")),
                                    ft.PopupMenuItem(content=ft.Text("Paiements"), on_click=lambda e: navigate_to(page, "paiements")),
                                    ft.PopupMenuItem(content=ft.Text("Concessions"), on_click=lambda e: navigate_to(page, "concessions")),
                                    ft.PopupMenuItem(content=ft.Text("Exhumations"), on_click=lambda e: navigate_to(page, "exhumations")),
                                    ft.PopupMenuItem(content=ft.Text("Deconnexion"), on_click=on_logout),
                                ],
                            ),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15,
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
        admin_dashboard(page)
    elif destination == "map":
        page.run_task(ouvrir_carte_directe, page)
    elif destination == "caveaux": 
        from pages.gestion_caveaux import gestion_caveaux_page
        gestion_caveaux_page(page)
    elif destination == "categories": 
        from pages.gestion_categories import gestion_categories_page
        gestion_categories_page(page)
    elif destination == "reservations":
        reservations_page(page)
    elif destination == "paiements":
        gestion_paiements_page(page)    
    elif destination == "concessions":
        gestion_concessions_page(page)
    elif destination == "exhumations":
        gestion_exhumations_page(page)
    elif destination == "users":
        from pages.gestion_utilisateurs import gestion_utilisateurs_page
        gestion_utilisateurs_page(page)
    elif destination == "audits":
        from pages.gestion_audits import gestion_audits_page
        gestion_audits_page(page)


async def ouvrir_carte_directe(page: ft.Page):
    """Ouvre la carte avec le HTML contenant le bouton de rafraîchissement"""
    try:
        html_content = get_carte_html()
        
        temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        html_path = os.path.join(temp_dir, "map.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        url = f"file:///{html_path.replace(os.sep, '/')}"
        webbrowser.open(url)
        show_snackbar(page, "Carte ouverte - cliquez sur Rafraîchir pour voir les changements", ft.Colors.GREEN)
        
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


def refresh_current_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    title = page.title
    if "Dashboard" in title:
        admin_dashboard(page)
    elif "Caveaux" in title:
        from pages.gestion_caveaux import gestion_caveaux_page
        gestion_caveaux_page(page)
    elif "Reservations" in title:
        reservations_page(page)
    elif "Paiements" in title:
        gestion_paiements_page(page)  
    elif "Concessions" in title:
        gestion_concessions_page(page)
    elif "Exhumations" in title:
        gestion_exhumations_page(page)
    else:
        admin_dashboard(page)


# ============================================
# DASHBOARD ADMIN
# ============================================

def admin_dashboard(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    page.title = "Admin Dashboard"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        refresh_current_page(page)
    page.on_resize = on_resize
    
    main_content = ft.Column([
        ft.Row([ft.Text("Tableau de bord Administrateur", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD)]),
        ft.Divider(height=20),
        ft.ProgressRing(),
        ft.Text("Chargement des statistiques..."),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True, spacing=10)
    
    page.controls.append(
        ft.Column([
            get_header_admin(page, "dashboard"),
            ft.Container(
                content=main_content,
                expand=True,
                padding=15 if is_mobile else 20,
            ),
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_admin_stats, page)


async def load_admin_stats(page: ft.Page):
    try:
        caveaux = await get_caveaux()
        stats = await get_paiements_stats()
        reservations_attente = await get_reservations_attente()
        reservations = await get_reservations()
        
        total_caveaux = len(caveaux)
        disponibles = len([c for c in caveaux if c["statut"] == "disponible"])
        reserves = len([c for c in caveaux if c["statut"] == "reserve"])
        occupes = len([c for c in caveaux if c["statut"] == "occupe"])
        non_exploitables = len([c for c in caveaux if c["statut"] == "non_exploitable"])
        
        total_reservations = len(reservations)
        en_attente = len([r for r in reservations if r["statut"] == "en_attente"])
        validees = len([r for r in reservations if r["statut"] == "validee"])
        annulees = len([r for r in reservations if r["statut"] == "annulee"])
        refusees = len([r for r in reservations if r["statut"] == "refusee"])
        
        total_paiements = stats.get("total_paiements", 0)
        total_montant = stats.get("total_montant_valide", 0)
        paiements_attente = stats.get("en_attente", 0)
        paiements_valides = stats.get("valides", 0)
        
        is_mobile = page.width < 768
        
        def create_stat_card(title, value, color=ft.Colors.GREY_700, value_size=28):
            return ft.Card(
                content=ft.Container(
                    ft.Column([
                        ft.Text(title, size=14 if not is_mobile else 12, color=color, text_align=ft.TextAlign.CENTER),
                        ft.Text(str(value), size=value_size if not is_mobile else 22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=15 if is_mobile else 20,
                    width=160 if not is_mobile else (page.width - 40) // 2 - 10,
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
                get_header_admin(page, "dashboard"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Tableau de bord Administrateur", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=20),
                        
                        ft.Text("Caveaux", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_stat_card("Total", total_caveaux, ft.Colors.BLUE),
                            create_stat_card("Disponibles", disponibles, ft.Colors.GREEN),
                            create_stat_card("Réservés", reserves, ft.Colors.ORANGE),
                            create_stat_card("Occupés", occupes, ft.Colors.RED),
                            create_stat_card("Non expl.", non_exploitables, ft.Colors.GREY_600),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20),
                        
                        ft.Text("Réservations", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_stat_card("Total", total_reservations, ft.Colors.BLUE),
                            create_stat_card("En attente", en_attente, ft.Colors.ORANGE),
                            create_stat_card("Validées", validees, ft.Colors.GREEN),
                            create_stat_card("Annulées", annulees, ft.Colors.RED),
                            create_stat_card("Refusées", refusees, ft.Colors.RED_700),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20),
                        
                        ft.Text("Paiements", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_stat_card("Total", total_paiements, ft.Colors.BLUE),
                            create_stat_card("En attente", paiements_attente, ft.Colors.ORANGE),
                            create_stat_card("Validés", paiements_valides, ft.Colors.GREEN),
                            create_stat_card("Montant total", f"{total_montant:,.0f} FCFA", ft.Colors.GREEN, 20),
                        ], wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20),
                        
                        ft.Text("Actions rapides", size=18 if not is_mobile else 16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            create_action_card("Voir la carte", "Carte", lambda e: navigate_to(page, "map"), "#79831C"),
                            create_action_card("Utilisateurs", "Gérer", lambda e: navigate_to(page, "users"), "#1976D2"),
                            create_action_card("Categories", "Gérer", lambda e: navigate_to(page, "categories"), "#9C27B0"),
                            create_action_card("Reservations", "Voir", lambda e: navigate_to(page, "reservations"), "#11695D"),
                            create_action_card("Paiements", "Gérer", lambda e: navigate_to(page, "paiements"), "#FF6F00"),
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
                get_header_admin(page, "dashboard"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Erreur de chargement", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(str(e), size=14),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_admin_stats, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    expand=True,
                    padding=20,
                )
            ], expand=True, spacing=0)
        )
        page.update()


# ============================================
# GESTION DES RESERVATIONS
# ============================================

def reservations_page(page: ft.Page):
    user = session.get("user")
    if not user:
        from pages.auth import login_page
        login_page(page)
        return
    
    page.title = "Gestion des reservations"
    page.controls.clear()
    is_mobile = page.width < 768
    
    def on_resize(e):
        user_check = session.get("user")
        if not user_check:
            from pages.auth import login_page
            login_page(page)
            return
        refresh_current_page(page)
    page.on_resize = on_resize
    
    page.controls.append(
        ft.Column([
            get_header_admin(page, "reservations"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                        ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_reservations_list, page), bgcolor="#1976D2", color="white"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    ft.ProgressRing(),
                    ft.Text("Chargement..."),
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=15 if is_mobile else 20,
            )
        ], expand=True, spacing=0)
    )
    page.update()
    page.run_task(load_reservations_list, page)


async def load_reservations_list(page: ft.Page):
    try:
        reservations = await get_reservations()
        is_mobile = page.width < 768
        
        if not reservations:
            page.controls.clear()
            page.controls.append(
                ft.Column([
                    get_header_admin(page, "reservations"),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Gestion des reservations", size=24 if not is_mobile else 20, weight=ft.FontWeight.BOLD),
                                ft.Button("Rafraichir", on_click=lambda e: page.run_task(load_reservations_list, page), bgcolor="#1976D2", color="white"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Text("Aucune reservation trouvee", size=16, color=ft.Colors.GREY_600),
                        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=15 if is_mobile else 20,
                    )
                ], expand=True, spacing=0)
            )
            page.update()
            return
        
        items = []
        for r in reservations:
            color = {
                "en_attente": ft.Colors.ORANGE,
                "validee": ft.Colors.GREEN,
                "annulee": ft.Colors.RED,
                "refusee": ft.Colors.RED,
            }.get(r["statut"], ft.Colors.GREY)
            
            actions_row = [
                ft.Button("Details", on_click=lambda e, rid=r['id']: show_reservation_detail(page, rid), bgcolor="#1976D2", color="white", expand=is_mobile),
            ]
            # FIX : les boutons Valider/Refuser sont maintenant masques (pas
            # juste grises) une fois la reservation traitee - seul le badge
            # de statut reste visible.
            if r["statut"] == "en_attente":
                actions_row.append(ft.Button("Valider", on_click=lambda e, rid=r['id']: page.run_task(handle_valider_reservation, page, rid), bgcolor="#4CAF50", color="white", expand=is_mobile))
                actions_row.append(ft.Button("Refuser", on_click=lambda e, rid=r['id']: page.run_task(handle_refuser_reservation, page, rid), bgcolor="#F44336", color="white", expand=is_mobile))

            items.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Text(f"Reservation #{r['id']}", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    ft.Text(r["statut"], size=12, color="white"),
                                    bgcolor=color,
                                    padding=5,
                                    border_radius=5,
                                ),
                            ]),
                            ft.Text(f"Defunt: {r['nom_defunt']}"),
                            ft.Text(f"Caveau: {r['caveau_reference']}"),
                            ft.Text(f"Client: {r['client_username']}"),
                            ft.Text(f"Date: {r['date_reservation'][:10]}"),
                            ft.Row(actions_row, spacing=5),
                        ]),
                        padding=10,
                        width=400 if not is_mobile else page.width - 40,
                    )
                )
            )
        
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_admin(page, "reservations"),
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
                )
            ], expand=True, spacing=0)
        )
        page.update()
        
    except Exception as e:
        page.controls.clear()
        page.controls.append(
            ft.Column([
                get_header_admin(page, "reservations"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Erreur: {e}", color=ft.Colors.RED),
                        ft.Button("Reessayer", on_click=lambda e: page.run_task(load_reservations_list, page), bgcolor="#1976D2", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    padding=20,
                )
            ], expand=True, spacing=0)
        )
        page.update()


def show_reservation_detail(page: ft.Page, reservation_id: int):
    page.run_task(handle_show_reservation_detail, page, reservation_id)


async def handle_show_reservation_detail(page: ft.Page, reservation_id: int):
    try:
        r = await get_reservation(reservation_id)
        is_mobile = page.width < 768
        
        color = {
            "en_attente": ft.Colors.ORANGE,
            "validee": ft.Colors.GREEN,
            "annulee": ft.Colors.RED,
            "refusee": ft.Colors.RED,
        }.get(r["statut"], ft.Colors.GREY)
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Reservation #{r['id']}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("Statut:", weight=ft.FontWeight.BOLD), ft.Container(ft.Text(r["statut"], color="white"), bgcolor=color, padding=5, border_radius=5)]),
                    ft.Text(f"Defunt: {r['nom_defunt']} {r.get('prenom_defunt', '')}"),
                    ft.Text(f"Caveau: {r['caveau_reference']}"),
                    ft.Text(f"Client: {r['client_username']}"),
                    ft.Text(f"Date deces: {r['date_deces']}"),
                    ft.Text(f"Date enterrement: {r['date_enterrement']}"),
                    ft.Text(f"Date reservation: {r['date_reservation']}"),
                    ft.Text(f"Telephone: {r.get('telephone', 'N/A')}"),
                    ft.Text(f"Email: {r.get('email_contact', 'N/A')}"),
                ], scroll=ft.ScrollMode.AUTO, height=300),
                width=400 if not is_mobile else page.width - 40,
            ),
            actions=[
                ft.Button("Fermer", on_click=lambda e: page.close(dialog)),
            ],
        )
        # FIX : "page.dialog = ...; dialog.open = True" est l'ancienne API,
        # peu fiable / depreciee sur les versions recentes de Flet (celles
        # qui utilisent ft.Colors avec un grand C, comme ici). page.open()
        # est la methode actuellement recommandee pour afficher un dialogue.
        page.open(dialog)
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


async def handle_valider_reservation(page: ft.Page, reservation_id: int):
    try:
        result = await valider_reservation(reservation_id)
        if not result or "error" in result:
            erreur = result.get("error", "Aucune reponse du serveur") if result else "Aucune reponse du serveur"
            show_snackbar(page, erreur, ft.Colors.RED)
            return
        await load_reservations_list(page)
        show_snackbar(page, f"Reservation #{reservation_id} validee", ft.Colors.GREEN)
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


async def handle_refuser_reservation(page: ft.Page, reservation_id: int):
    try:
        result = await refuser_reservation(reservation_id, "Refuse par l'administrateur")
        if not result or "error" in result:
            erreur = result.get("error", "Aucune reponse du serveur") if result else "Aucune reponse du serveur"
            show_snackbar(page, erreur, ft.Colors.RED)
            return
        await load_reservations_list(page)
        show_snackbar(page, f"Reservation #{reservation_id} refusee", ft.Colors.RED)
    except Exception as e:
        show_snackbar(page, f"Erreur: {e}", ft.Colors.RED)


# FONCTIONS UTILES
def close_dialog(page: ft.Page):
    # Conserve pour compatibilite si appelee ailleurs, mais les nouveaux
    # dialogues utilisent directement page.close(dialog).
    if page.dialog:
        page.close(page.dialog)

def show_snackbar(page: ft.Page, message: str, color):
    page.snack_bar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=color,
        duration=3000,
        open=True,
    )
    page.update()

def login_page(page: ft.Page):
    from pages.auth import login_page as auth_login
    auth_login(page)