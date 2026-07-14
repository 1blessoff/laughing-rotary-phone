"""
Vue Django qui sert la carte interactive des caveaux en HTML/Leaflet.

Contrairement à l'ancienne implémentation admin (carte écrite dans un fichier
temporaire puis ouverte dans un navigateur externe, avec un bouton
"Rafraîchir" manuel), cette version :
  1. Est servie directement par Django (une URL, pas de fichier temporaire) ;
  2. Se rafraîchit TOUTE SEULE toutes les 5 secondes (setInterval), donc
     reflète les changements de statut en quasi temps réel sans action de
     l'utilisateur.

À placer dans l'app qui gère les caveaux (probablement `terrains/`).
Ajoutez ensuite dans vos urls.py :

    from terrains.views_carte import carte_caveaux_view
    urlpatterns += [
        path("carte-caveaux/", carte_caveaux_view, name="carte-caveaux"),
    ]

Le résultat sera accessible à : http://127.0.0.1:8000/carte-caveaux/
(adaptez le chemin si vous le montez ailleurs, par ex. sous /api/).
"""

from django.http import HttpResponse

REFRESH_INTERVAL_MS = 5000  # 5 secondes


def carte_caveaux_view(request):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carte des caveaux</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{ height: 100%; width: 100%; }}
            #map {{ height: 100%; width: 100%; }}
            .legend {{
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
            }}
            .legend-item {{ display: flex; align-items: center; margin: 4px 0; }}
            .legend-color {{ width: 16px; height: 16px; border-radius: 50%; margin-right: 10px; border: 1px solid rgba(0,0,0,0.2); }}
            .popup-content {{ font-family: Arial, sans-serif; font-size: 13px; }}
            .popup-content strong {{ color: #1a237e; }}
            .popup-statut {{ display: inline-block; padding: 2px 8px; border-radius: 4px; color: white; font-size: 11px; font-weight: bold; margin-top: 3px; }}
            .popup-statut.disponible {{ background: #4CAF50; }}
            .popup-statut.reserve {{ background: #FF9800; }}
            .popup-statut.occupe {{ background: #F44336; }}
            .popup-statut.non_exploitable {{ background: #9E9E9E; }}
            .live-badge {{
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background: #1976D2;
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 13px;
                font-family: Arial, sans-serif;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .live-dot {{
                width: 8px; height: 8px; border-radius: 50%;
                background: #4CAF50;
                animation: pulse 1.5s infinite;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.3; }}
                100% {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <div class="live-badge"><span class="live-dot"></span> Mise à jour auto (5s)</div>
        <div id="map"></div>
        <div class="legend">
            <div class="legend-item"><div class="legend-color" style="background:#4CAF50;"></div> Disponible</div>
            <div class="legend-item"><div class="legend-color" style="background:#FF9800;"></div> Réservé</div>
            <div class="legend-item"><div class="legend-color" style="background:#F44336;"></div> Occupé</div>
            <div class="legend-item"><div class="legend-color" style="background:#9E9E9E;"></div> Non exploitable</div>
        </div>
        <script>
            var map = null;
            var markers = [];

            function initMap() {{
                map = L.map('map').setView([-4.2634, 15.2429], 13);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19,
                }}).addTo(map);
                chargerCaveaux(true);
                // FIX : auto-rafraichissement reel, plus besoin de cliquer.
                setInterval(function() {{ chargerCaveaux(false); }}, {REFRESH_INTERVAL_MS});
            }}

            function chargerCaveaux(fitBoundsOnLoad) {{
                // Envoyer les cookies de session pour que Django identifie l'utilisateur
                fetch('/api/caveaux/', {{ credentials: 'same-origin' }})
                .then(response => response.json())
                .then(data => {{
                    markers.forEach(function(m) {{ map.removeLayer(m); }});
                    markers = [];

                    var bounds = [];
                    data.forEach(function(caveau) {{
                        if (caveau.latitude && caveau.longitude) {{
                            var color = '#4CAF50';
                            var statutClasse = 'disponible';
                            if (caveau.statut === 'reserve') {{ color = '#FF9800'; statutClasse = 'reserve'; }}
                            else if (caveau.statut === 'occupe') {{ color = '#F44336'; statutClasse = 'occupe'; }}
                            else if (caveau.statut === 'non_exploitable') {{ color = '#9E9E9E'; statutClasse = 'non_exploitable'; }}

                            var marker = L.circleMarker([caveau.latitude, caveau.longitude], {{
                                radius: 12,
                                fillColor: color,
                                color: '#FFFFFF',
                                weight: 2,
                                opacity: 1,
                                fillOpacity: 0.9
                            }}).addTo(map);

                            var prix = caveau.prix_base || 0;
                            var prix_affichage = prix > 0 ? prix.toLocaleString() + ' FCFA' : 'Prix non défini';

                            marker.bindPopup(
                                '<div class="popup-content">' +
                                '<strong>' + caveau.reference + '</strong><br>' +
                                'Statut: <span class="popup-statut ' + statutClasse + '">' + caveau.statut + '</span><br>' +
                                'Section: ' + caveau.section + '<br>' +
                                'Bloc: ' + (caveau.bloc || 'N/A') + '<br>' +
                                'Prix: ' + prix_affichage +
                                '</div>',
                                {{ maxWidth: 300 }}
                            );
                            markers.push(marker);
                            bounds.push([caveau.latitude, caveau.longitude]);
                        }}
                    }});

                    if (fitBoundsOnLoad && bounds.length > 0) {{
                        map.fitBounds(bounds, {{ padding: [30, 30] }});
                    }}
                }})
                .catch(function(error) {{ console.error('Erreur chargement caveaux:', error); }});
            }}

            window.onload = function() {{ initMap(); }};
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)