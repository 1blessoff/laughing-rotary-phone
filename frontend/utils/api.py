import aiohttp
import aiohttp.client_exceptions
import asyncio
import json



API_URL = "https://laughing-rotary-phone.onrender.com"


# Session globale pour partager les cookies entre toutes les requêtes
_session = None

async def get_session():
    global _session
    if _session is None or _session.closed:
        # Créer un CookieJar qui garde les cookies entre les requêtes.
        # unsafe=True améliore la compatibilité locale avec les cookies de session.
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        _session = aiohttp.ClientSession(cookie_jar=cookie_jar, trust_env=False)
        print("Nouvelle session créée")
    return _session

async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None
        print("Session fermée")

async def get_cookies():
    """Debug: récupérer les cookies actuels"""
    session = await get_session()
    if session and session._cookie_jar:
        cookies = {k: v.value for k, v in session._cookie_jar}
        print(f"Cookies actuels: {cookies}")
        return cookies
    return {}

async def post_request(endpoint: str, data: dict = None, params: dict = None):
    """Fonction generique pour les requetes POST asynchrones"""
    url = f"{API_URL}/{endpoint}"
    print(f"\n{'='*60}")
    print(f"POST {endpoint}")
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    if data:
        print(f"Data: {data}")
    
    try:
        session = await get_session()
        
        # Debug: afficher les cookies avant la requête
        cookies_before = {k: v.value for k, v in session._cookie_jar.filter_cookies(url).items()}
        print(f"Cookies avant requete: {cookies_before}")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.post(url, params=params, json=data, timeout=timeout) as response:
            print(f"Status: {response.status}")
            
            # Debug: afficher les cookies reçus
            cookies_recus = {k: v.value for k, v in response.cookies.items()}
            print(f"Cookies recus: {cookies_recus}")
            
            # Debug: header Set-Cookie (si present)
            set_cookie = response.headers.get('Set-Cookie')
            if set_cookie:
                print(f"Set-Cookie header: {set_cookie}")
            
            cookies_after = {k: v.value for k, v in session._cookie_jar.filter_cookies(url).items()}
            print(f"Cookies après requete: {cookies_after}")
            
            try:
                result = await response.json()
                print(f"Result: {result}")
                return result
            except Exception as e:
                text = await response.text()
                print(f"Response text: {text}")
                return {"error": f"Erreur de parsing: {e}"}
                
    except asyncio.TimeoutError:
        print("ERREUR: Timeout")
        return {"error": "Le serveur ne répond pas (timeout)"}
    except aiohttp.ClientError as e:
        print(f"ERREUR ClientError: {e}")
        return {"error": f"Erreur de connexion: {e}"}
    except Exception as e:
        print(f"ERREUR: {e}")
        return {"error": str(e)}

async def get_request(endpoint: str, params: dict = None):
    """Fonction generique pour les requetes GET asynchrones"""
    url = f"{API_URL}/{endpoint}"
    print(f"\n{'='*60}")
    print(f"GET {endpoint}")
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    
    try:
        session = await get_session()
        cookies_before = {k: v.value for k, v in session._cookie_jar.filter_cookies(url).items()}
        print(f"🍪 Cookies avant requete GET: {cookies_before}")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(url, params=params, timeout=timeout) as response:
            print(f"📊 Status: {response.status}")
            
            cookies_after = {k: v.value for k, v in session._cookie_jar.filter_cookies(url).items()}
            print(f"🍪 Cookies après requete GET: {cookies_after}")
            
            set_cookie = response.headers.get('Set-Cookie')
            if set_cookie:
                print(f"📋 Set-Cookie header: {set_cookie}")
                
            try:
                result = await response.json()
                print(f"✅ Result: {result}")
                return result
            except Exception:
                text = await response.text()
                print(f"❌ Response text: {text}")
                return {"error": f"Erreur de parsing: {text}"}
                
    except asyncio.TimeoutError:
        print("⏰ ERREUR: Timeout")
        return {"error": "Le serveur ne répond pas (timeout)"}
    except aiohttp.ClientError as e:
        print(f"❌ ERREUR ClientError: {e}")
        return {"error": f"Erreur de connexion: {e}"}
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return {"error": str(e)}

async def put_request(endpoint: str, data: dict = None, params: dict = None):
    """Fonction generique pour les requetes PUT asynchrones"""
    url = f"{API_URL}/{endpoint}"
    print(f"\n{'='*60}")
    print(f"📤 PUT {endpoint}")
    print(f"📍 URL: {url}")
    if params:
        print(f"📋 Params: {params}")
    if data:
        print(f"📦 Data: {data}")
    
    try:
        session = await get_session()
        cookies_before = {k: v.value for k, v in session._cookie_jar.filter_cookies(url).items()}
        print(f"🍪 Cookies avant requete PUT: {cookies_before}")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.put(url, params=params, json=data, timeout=timeout) as response:
            print(f"📊 Status: {response.status}")
            
            cookies_after = {k: v.value for k, v in session._cookie_jar.filter_cookies(url).items()}
            print(f"🍪 Cookies après requete PUT: {cookies_after}")
            
            try:
                result = await response.json()
                print(f"✅ Result: {result}")
                return result
            except Exception as e:
                text = await response.text()
                print(f"❌ Response text: {text}")
                return {"error": f"Erreur de parsing: {e}"}
                
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return {"error": str(e)}

async def delete_request(endpoint: str, params: dict = None):
    """Fonction generique pour les requetes DELETE asynchrones"""
    url = f"{API_URL}/{endpoint}"
    print(f"\n{'='*60}")
    print(f"📤 DELETE {endpoint}")
    print(f"📍 URL: {url}")
    if params:
        print(f"📋 Params: {params}")
    
    try:
        session = await get_session()
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.delete(url, params=params, timeout=timeout) as response:
            print(f"📊 Status: {response.status}")
            try:
                result = await response.json()
                print(f"✅ Result: {result}")
                return result
            except Exception as e:
                text = await response.text()
                print(f"❌ Response text: {text}")
                return {"error": f"Erreur de parsing: {e}"}
                
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return {"error": str(e)}


# ============================================
# AUTHENTIFICATION
# ============================================

async def login(username: str, password: str):
    print(f"\n LOGIN: {username}")
    await close_session()
    return await post_request("auth/login", {"username": username, "password": password})

async def register(data: dict):
    print(f"\n REGISTER: {data.get('username')}")
    return await post_request("auth/register", data)

async def verify_mfa(code: str, user_id: int):
    print(f"\n VERIFY MFA: code={code}, user_id={user_id}")
    return await post_request("auth/verify-mfa", {"mfa_code": code, "user_id": user_id})

async def request_password_reset(email: str):
    print(f"\n PASSWORD RESET REQUEST: {email}")
    return await post_request("auth/request-password-reset", {"email": email})

async def confirm_password_reset(email: str, code: str, new_password: str):
    print(f"\n PASSWORD RESET CONFIRM: {email}")
    return await post_request("auth/confirm-password-reset", {
        "email": email,
        "code": code,
        "new_password": new_password
    })

async def logout():
    print(f"\n LOGOUT")
    result = await post_request("auth/logout", {})
    await close_session()
    return result

async def get_current_user():
    print(f"\n GET CURRENT USER")
    return await get_request("auth/me")


# ============================================
# CAVEAUX
# ============================================

async def get_caveaux(params: dict = None):
    print(f"\n GET CAVEAUX")
    return await get_request("caveaux/", params)

async def get_caveaux_disponibles():
    print(f"\n GET CAVEAUX DISPONIBLES")
    return await get_request("caveaux/", {"disponibles_seulement": "true"})

async def create_caveau(data: dict):
    print(f"\n CREATE CAVEAU: {data.get('reference')}")
    return await post_request("caveaux/", data)

async def delete_caveau(caveau_id: int):
    print(f"\n DELETE CAVEAU: {caveau_id}")
    return await delete_request(f"caveaux/{caveau_id}")

async def update_caveau(caveau_id: int, data: dict):
    print(f"\n UPDATE CAVEAU: {caveau_id}")
    return await put_request(f"caveaux/{caveau_id}", data)

async def changer_statut_caveau(caveau_id: int, nouveau_statut: str):
    print(f"\n CHANGER STATUT CAVEAU: {caveau_id} -> {nouveau_statut}")
    return await put_request(f"caveaux/{caveau_id}/statut", {"nouveau_statut": nouveau_statut})


# ============================================
# RESERVATIONS
# ============================================

async def create_reservation(data: dict):
    print(f"\n  CREATE RESERVATION: {data.get('nom_defunt')}")
    return await post_request("reservations/", data)

async def get_reservations():
    print(f"\n GET RESERVATIONS")
    return await get_request("reservations/")

async def get_reservation(reservation_id: int):
    print(f"\n GET RESERVATION: {reservation_id}")
    return await get_request(f"reservations/{reservation_id}")

async def get_reservations_attente():
    print(f"\n GET RESERVATIONS ATTENTE")
    return await get_request("reservations/attente")

async def valider_reservation(reservation_id: int):
    print(f"\n VALIDER RESERVATION: {reservation_id}")
    return await put_request(f"reservations/{reservation_id}/valider")

async def refuser_reservation(reservation_id: int, motif: str = ""):
    print(f"\n REFUSER RESERVATION: {reservation_id}")
    return await put_request(f"reservations/{reservation_id}/refuser", {"motif": motif})

async def annuler_reservation(reservation_id: int, motif: str = ""):
    print(f"\n ANNULER RESERVATION: {reservation_id}")
    return await put_request(f"reservations/{reservation_id}/annuler", {"motif": motif})


# ============================================
# CONCESSIONS
# ============================================

async def create_concession(data: dict):
    print(f"\n CREATE CONCESSION: {data.get('reservation_id')}")
    return await post_request("concessions/", data)

async def get_concessions():
    print(f"\n GET CONCESSIONS")
    return await get_request("concessions/")

async def get_concession(concession_id: int):
    print(f"\n GET CONCESSION: {concession_id}")
    return await get_request(f"concessions/{concession_id}")

async def renouveler_concession(concession_id: int, data: dict):
    print(f"\n RENOUVELER CONCESSION: {concession_id}")
    return await put_request(f"concessions/{concession_id}/renouveler", data)


# ============================================
# PAIEMENTS
# ============================================

async def create_paiement(data: dict):
    print(f"\n CREATE PAIEMENT: {data.get('reservation_id')}")
    return await post_request("paiements/", data)

async def valider_paiement(paiement_id: int):
    print(f"\n VALIDER PAIEMENT: {paiement_id}")
    return await put_request(f"paiements/{paiement_id}/valider")

async def refuser_paiement(paiement_id: int):
    print(f"\n REFUSER PAIEMENT: {paiement_id}")
    return await put_request(f"paiements/{paiement_id}/refuser")

async def get_paiements():
    print(f"\nGET PAIEMENTS")
    return await get_request("paiements/")

async def get_paiements_stats():
    print(f"\nGET PAIEMENTS STATS")
    return await get_request("paiements/stats")

async def get_paiements_reservation(reservation_id: int):
    print(f"\nGET PAIEMENTS RESERVATION: {reservation_id}")
    return await get_request(f"paiements/reservation/{reservation_id}")

async def get_paiement(paiement_id: int):
    print(f"\nGET PAIEMENT: {paiement_id}")
    return await get_request(f"paiements/{paiement_id}")

async def delete_paiement(paiement_id: int):
    print(f"\nDELETE PAIEMENT: {paiement_id}")
    return await delete_request(f"paiements/{paiement_id}")

async def update_paiement(paiement_id: int, data: dict):
    print(f"\nUPDATE PAIEMENT: {paiement_id}")
    return await put_request(f"paiements/{paiement_id}", data)

async def get_mes_paiements():
    print(f"\nGET MES PAIEMENTS")
    return await get_request("paiements/mes-paiements")


# ============================================
# EXHUMATIONS
# ============================================

async def create_exhumation(data: dict):
    print(f"\nCREATE EXHUMATION: {data.get('concession_id')}")
    return await post_request("concessions/exhumations", data)

async def get_exhumations():
    print(f"\nGET EXHUMATIONS")
    return await get_request("concessions/exhumations")

async def approuver_exhumation(exhumation_id: int):
    print(f"\nAPPROUVER EXHUMATION: {exhumation_id}")
    return await put_request(f"concessions/exhumations/{exhumation_id}/approuver")

async def refuser_exhumation(exhumation_id: int, motif: str = ""):
    print(f"\nREFUSER EXHUMATION: {exhumation_id}")
    return await put_request(f"concessions/exhumations/{exhumation_id}/refuser", {"motif": motif})

async def realiser_exhumation(exhumation_id: int):
    print(f"\nREALISER EXHUMATION: {exhumation_id}")
    return await put_request(f"concessions/exhumations/{exhumation_id}/realiser")


# ============================================
# UTILISATEURS
# ============================================

async def get_users():
    print(f"\nGET USERS")
    return await get_request("auth/users")

async def change_user_role(user_id: int, role: str):
    print(f"\nCHANGE USER ROLE: {user_id} -> {role}")
    # Utilisation des query params pour le rôle
    return await put_request(f"auth/users/{user_id}/role", params={"role": role})

async def toggle_user_active(user_id: int):
    print(f"\nTOGGLE USER ACTIVE: {user_id}")
    return await put_request(f"auth/users/{user_id}/activate")