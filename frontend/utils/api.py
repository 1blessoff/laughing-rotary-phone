import aiohttp
import asyncio
import json

API_URL = "https://laughing-rotary-phone.onrender.com/api"

_session = None

async def get_session():
    global _session
    if _session is None or _session.closed:
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        # Timeout optimisé : 15 secondes au lieu de 120
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        _session = aiohttp.ClientSession(
            cookie_jar=cookie_jar, 
            trust_env=False, 
            timeout=timeout
        )
    return _session

async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None

async def post_request(endpoint: str, data: dict = None, params: dict = None):
    url = f"{API_URL}/{endpoint}"
    try:
        session = await get_session()
        async with session.post(url, params=params, json=data) as response:
            try:
                return await response.json()
            except Exception:
                text = await response.text()
                return {"error": f"Erreur de réponse serveur: {text}"}
    except asyncio.TimeoutError:
        return {"error": "Le serveur met trop de temps à répondre (Timeout)"}
    except aiohttp.ClientError as e:
        return {"error": f"Erreur réseau: {e}"}
    except Exception as e:
        return {"error": str(e)}

async def get_request(endpoint: str, params: dict = None):
    url = f"{API_URL}/{endpoint}"
    try:
        session = await get_session()
        async with session.get(url, params=params) as response:
            try:
                return await response.json()
            except Exception:
                text = await response.text()
                return {"error": f"Erreur de réponse serveur: {text}"}
    except asyncio.TimeoutError:
        return {"error": "Le serveur met trop de temps à répondre (Timeout)"}
    except aiohttp.ClientError as e:
        return {"error": f"Erreur réseau: {e}"}
    except Exception as e:
        return {"error": str(e)}

async def put_request(endpoint: str, data: dict = None, params: dict = None):
    url = f"{API_URL}/{endpoint}"
    try:
        session = await get_session()
        async with session.put(url, params=params, json=data) as response:
            try:
                return await response.json()
            except Exception:
                text = await response.text()
                return {"error": f"Erreur de réponse serveur: {text}"}
    except Exception as e:
        return {"error": str(e)}

async def delete_request(endpoint: str, params: dict = None):
    url = f"{API_URL}/{endpoint}"
    try:
        session = await get_session()
        async with session.delete(url, params=params) as response:
            try:
                return await response.json()
            except Exception:
                text = await response.text()
                return {"error": f"Erreur de réponse serveur: {text}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================
# AUTHENTIFICATION
# ============================================

async def login(username: str, password: str):
    return await post_request("auth/login", {"username": username, "password": password})

async def register(data: dict):
    return await post_request("auth/register", data)

async def verify_mfa(code: str, user_id: int):
    return await post_request("auth/verify-mfa", {"mfa_code": code, "user_id": user_id})

async def request_password_reset(email: str):
    return await post_request("auth/request-password-reset", {"email": email})

async def confirm_password_reset(email: str, code: str, new_password: str):
    return await post_request("auth/confirm-password-reset", {
        "email": email,
        "code": code,
        "new_password": new_password
    })

async def logout():
    result = await post_request("auth/logout", {})
    await close_session()
    return result

async def get_current_user():
    return await get_request("auth/me")


# ============================================
# CAVEAUX
# ============================================

async def get_caveaux(params: dict = None):
    return await get_request("caveaux/", params)

async def get_caveaux_disponibles():
    return await get_request("caveaux/", {"disponibles_seulement": "true"})

async def create_caveau(data: dict):
    return await post_request("caveaux/", data)

async def delete_caveau(caveau_id: int):
    return await delete_request(f"caveaux/{caveau_id}")

async def update_caveau(caveau_id: int, data: dict):
    return await put_request(f"caveaux/{caveau_id}", data)

async def changer_statut_caveau(caveau_id: int, nouveau_statut: str):
    return await put_request(f"caveaux/{caveau_id}/statut", {"nouveau_statut": nouveau_statut})


# ============================================
# RESERVATIONS
# ============================================

async def create_reservation(data: dict):
    return await post_request("reservations/", data)

async def get_reservations():
    return await get_request("reservations/")

async def get_reservation(reservation_id: int):
    return await get_request(f"reservations/{reservation_id}")

async def get_reservations_attente():
    return await get_request("reservations/attente")

async def valider_reservation(reservation_id: int):
    return await put_request(f"reservations/{reservation_id}/valider")

async def refuser_reservation(reservation_id: int, motif: str = ""):
    return await put_request(f"reservations/{reservation_id}/refuser", {"motif": motif})

async def annuler_reservation(reservation_id: int, motif: str = ""):
    return await put_request(f"reservations/{reservation_id}/annuler", {"motif": motif})


# ============================================
# CONCESSIONS
# ============================================

async def create_concession(data: dict):
    return await post_request("concessions/", data)

async def get_concessions():
    return await get_request("concessions/")

async def get_concession(concession_id: int):
    return await get_request(f"concessions/{concession_id}")

async def renouveler_concession(concession_id: int, data: dict):
    return await put_request(f"concessions/{concession_id}/renouveler", data)


# ============================================
# PAIEMENTS
# ============================================

async def create_paiement(data: dict):
    return await post_request("paiements/", data)

async def valider_paiement(paiement_id: int):
    return await put_request(f"paiements/{paiement_id}/valider")

async def refuser_paiement(paiement_id: int):
    return await put_request(f"paiements/{paiement_id}/refuser")

async def get_paiements():
    return await get_request("paiements/")

async def get_paiements_stats():
    return await get_request("paiements/stats")

async def get_paiements_reservation(reservation_id: int):
    return await get_request(f"paiements/reservation/{reservation_id}")

async def get_paiement(paiement_id: int):
    return await get_request(f"paiements/{paiement_id}")

async def delete_paiement(paiement_id: int):
    return await delete_request(f"paiements/{paiement_id}")

async def update_paiement(paiement_id: int, data: dict):
    return await put_request(f"paiements/{paiement_id}", data)

async def get_mes_paiements():
    return await get_request("paiements/mes-paiements")


# ============================================
# EXHUMATIONS
# ============================================

async def create_exhumation(data: dict):
    return await post_request("concessions/exhumations", data)

async def get_exhumations():
    return await get_request("concessions/exhumations")

async def approuver_exhumation(exhumation_id: int):
    return await put_request(f"concessions/exhumations/{exhumation_id}/approuver")

async def refuser_exhumation(exhumation_id: int, motif: str = ""):
    return await put_request(f"concessions/exhumations/{exhumation_id}/refuser", {"motif": motif})

async def realiser_exhumation(exhumation_id: int):
    return await put_request(f"concessions/exhumations/{exhumation_id}/realiser")


# ============================================
# UTILISATEURS
# ============================================

async def get_users():
    return await get_request("auth/users")

async def change_user_role(user_id: int, role: str):
    return await put_request(f"auth/users/{user_id}/role", params={"role": role})

async def toggle_user_active(user_id: int):
    return await put_request(f"auth/users/{user_id}/activate")