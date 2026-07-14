from audit.utils import log_action
from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model
from typing import List, Optional
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings

from .models import Reservation 
from terrains.models import Caveau
from .schemas import (
    ReservationSchema, ReservationCreateSchema, 
    ReservationUpdateSchema, ReservationActionSchema,
    ReservationFiltreSchema
)
from utils.notifications import NotificationService 

User = get_user_model()
router = Router()

# ============================================
# CRÉER UNE RÉSERVATION (Client)
# ============================================

@router.post("/", response={200: ReservationSchema, 400: dict, 403: dict})
def create_reservation(request, data: ReservationCreateSchema):
    """Creer une nouvelle reservation (Client)"""
    print("=== create_reservation ===")
    print(f"User: {request.user}")
    try:
        print(f"Session keys: {list(request.session.keys())}")
    except Exception:
        print("Session inaccessible")

    if not request.user.is_authenticated:
        print("User non authentifie - rejet de la requete")
        return 403, {"error": "Non authentifie"}
    
    if request.user.role not in ['client', 'admin', 'agent', 'secretariat']:
        return 403, {"error": "Vous n'etes pas autorise a faire une reservation"}
    
    caveau = get_object_or_404(Caveau, id=data.caveau_id)
    
    if not caveau.est_disponible:
        return 400, {"error": f"Le caveau {caveau.reference} n'est pas disponible (statut: {caveau.statut})"}
    
    # VERIFICATION : Empêcher double réservation pour le meme caveau
    existing = Reservation.objects.filter(
        client=request.user,
        caveau=caveau,
        statut__in=['en_attente', 'validee']
    ).exists()
    
    if existing:
        return 400, {"error": "Vous avez deja une reservation en cours pour ce caveau"}



    if Reservation.objects.filter(caveau=caveau, statut='en_attente').exists():
        return 400, {"error": f"Une reservation est deja en attente pour ce caveau"}
    
    reservation = Reservation.objects.create(
        client=request.user,
        caveau=caveau,
        statut='en_attente',
        nom_defunt=data.nom_defunt,
        prenom_defunt=data.prenom_defunt or "",
        date_naissance=data.date_naissance,
        date_deces=data.date_deces,
        date_enterrement=data.date_enterrement,
        nom_famille=data.nom_famille or "",
        adresse=data.adresse or "",
        telephone=data.telephone or "",
        email_contact=data.email_contact or request.user.email,
        notes=data.notes or "",
        besoin_ceremonie=data.besoin_ceremonie or False,
        besoin_voiture=data.besoin_voiture or False,
    )
    
    print(f"Reservation creee en base: id tentative (avant statut)")
    caveau.changer_statut('reserve', request.user)
    print(f"Caveau {caveau.reference} marque comme reserve par {request.user}")
    

    # ✅ Log
    log_action(
        request,
        action='create',
        model_name='Reservation',
        object_id=reservation.id,
        object_repr=f"Reservation #{reservation.id} - {reservation.nom_defunt}",
        changes={"client": request.user.username, "caveau": caveau.reference}
    )
    
    return 200, {...}




    # Notification à l'admin
    try:
        NotificationService.notification_nouvelle_reservation(reservation)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return 200, {
        "id": reservation.id,
        "client_id": reservation.client.id,
        "client_username": reservation.client.username,
        "caveau_id": reservation.caveau.id,
        "caveau_reference": reservation.caveau.reference,
        "statut": reservation.statut,
        "statut_color": reservation.get_statut_color(),
        "nom_defunt": reservation.nom_defunt,
        "prenom_defunt": reservation.prenom_defunt,
        "date_naissance": reservation.date_naissance,
        "date_deces": reservation.date_deces,
        "date_enterrement": reservation.date_enterrement,
        "nom_famille": reservation.nom_famille,
        "adresse": reservation.adresse,
        "telephone": reservation.telephone,
        "email_contact": reservation.email_contact,
        "notes": reservation.notes,
        "besoin_ceremonie": reservation.besoin_ceremonie,
        "besoin_voiture": reservation.besoin_voiture,
        "date_reservation": reservation.date_reservation,
        "date_validation": reservation.date_validation,
        "date_annulation": reservation.date_annulation,
        "valide_par": None,
        "valide_par_username": None,
        "facture_pdf": None,
        "certificat_pdf": None,
    }


# LISTER LES RESERVATIONS

@router.get("/", response={200: List[ReservationSchema], 403: dict})
def list_reservations(request, filters: ReservationFiltreSchema = Query(None)):
    """Lister les reservations avec filtres"""
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}
    
    reservations = Reservation.objects.all().order_by('-date_reservation')

    if request.user.role not in ['admin', 'agent', 'secretariat']:
        reservations = reservations.filter(client=request.user)

    if filters:
        if filters.statut:
            reservations = reservations.filter(statut=filters.statut)
        if filters.client_id and request.user.role in ['admin', 'agent', 'secretariat']:
            reservations = reservations.filter(client_id=filters.client_id)
        if filters.caveau_id:
            reservations = reservations.filter(caveau_id=filters.caveau_id)
        if filters.date_debut:
            reservations = reservations.filter(date_reservation__date__gte=filters.date_debut)
        if filters.date_fin:
            reservations = reservations.filter(date_reservation__date__lte=filters.date_fin)
        if filters.recherche:
            reservations = reservations.filter(
                Q(nom_defunt__icontains=filters.recherche) |
                Q(prenom_defunt__icontains=filters.recherche) |
                Q(nom_famille__icontains=filters.recherche) |
                Q(caveau__reference__icontains=filters.recherche)
            )


    result = []
    for r in reservations:
        result.append({
            "id": r.id,
            "client_id": r.client.id,
            "client_username": r.client.username,
            "caveau_id": r.caveau.id,
            "caveau_reference": r.caveau.reference,
            "statut": r.statut,
            "statut_color": r.get_statut_color(),
            "nom_defunt": r.nom_defunt,
            "prenom_defunt": r.prenom_defunt,
            "date_naissance": r.date_naissance,
            "date_deces": r.date_deces,
            "date_enterrement": r.date_enterrement,
            "nom_famille": r.nom_famille,
            "adresse": r.adresse,
            "telephone": r.telephone,
            "email_contact": r.email_contact,
            "notes": r.notes,
            "besoin_ceremonie": r.besoin_ceremonie,
            "besoin_voiture": r.besoin_voiture,
            "date_reservation": r.date_reservation,
            "date_validation": r.date_validation,
            "date_annulation": r.date_annulation,
            "valide_par": r.valide_par.id if r.valide_par else None,
            "valide_par_username": r.valide_par.username if r.valide_par else None,
            "facture_pdf": r.facture_pdf.url if r.facture_pdf else None,
            "certificat_pdf": r.certificat_pdf.url if r.certificat_pdf else None,
        })
    return 200, result



# ============================================
# RESERVATIONS EN ATTENTE (pour Admin)
# ============================================

@router.get("/attente")
def reservations_en_attente(request):
    """Liste des reservations en attente (Admin/Agent/Secretariat)"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    reservations = Reservation.objects.filter(statut='en_attente').order_by('date_reservation')
    
    result = []
    for r in reservations:
        result.append({
            "id": r.id,
            "caveau_reference": r.caveau.reference,
            "client_username": r.client.username,
            "nom_defunt": r.nom_defunt,
            "date_deces": r.date_deces,
            "date_enterrement": r.date_enterrement,
            "date_reservation": r.date_reservation,
        })
    
    return result





# ============================================
# DETAILS D'UNE RESERVATION
# ============================================

@router.get("/{reservation_id}", response={200: ReservationSchema, 403: dict})
def get_reservation(request, reservation_id: int):
    """Details d'une reservation"""
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and reservation.client != request.user:
        return 403, {"error": "Vous n'avez pas acces a cette reservation"}
    
    return 200, {
        "id": reservation.id,
        "client_id": reservation.client.id,
        "client_username": reservation.client.username,
        "caveau_id": reservation.caveau.id,
        "caveau_reference": reservation.caveau.reference,
        "statut": reservation.statut,
        "statut_color": reservation.get_statut_color(),
        "nom_defunt": reservation.nom_defunt,
        "prenom_defunt": reservation.prenom_defunt,
        "date_naissance": reservation.date_naissance,
        "date_deces": reservation.date_deces,
        "date_enterrement": reservation.date_enterrement,
        "nom_famille": reservation.nom_famille,
        "adresse": reservation.adresse,
        "telephone": reservation.telephone,
        "email_contact": reservation.email_contact,
        "notes": reservation.notes,
        "besoin_ceremonie": reservation.besoin_ceremonie,
        "besoin_voiture": reservation.besoin_voiture,
        "date_reservation": reservation.date_reservation,
        "date_validation": reservation.date_validation,
        "date_annulation": reservation.date_annulation,
        "valide_par": reservation.valide_par.id if reservation.valide_par else None,
        "valide_par_username": reservation.valide_par.username if reservation.valide_par else None,
        "facture_pdf": reservation.facture_pdf.url if reservation.facture_pdf else None,
        "certificat_pdf": reservation.certificat_pdf.url if reservation.certificat_pdf else None,
    }


# ============================================
# VALIDER UNE RESERVATION (Admin/Agent)
# ============================================

@router.put("/{reservation_id}/valider")
def valider_reservation(request, reservation_id: int, data: ReservationActionSchema = None):
    """Valider une reservation (Admin/Agent/Secretariat)"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if reservation.statut != 'en_attente':
        return {"error": f"Cette reservation est deja {reservation.statut}"}
    
    reservation.valider(request.user)
    
    # Notification au client
    try:
        NotificationService.notification_reservation_validee(reservation)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return {
        "success": True,
        "message": f"Reservation #{reservation.id} validee",
        "reservation_id": reservation.id,
        "statut": "validee"
    }


# ============================================
# REFUSER UNE RESERVATION (Admin/Agent)
# ============================================

@router.put("/{reservation_id}/refuser")
def refuser_reservation(request, reservation_id: int, data: ReservationActionSchema = None):
    """Refuser une reservation (Admin/Agent/Secretariat)"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if reservation.statut != 'en_attente':
        return {"error": f"Cette reservation est deja {reservation.statut}"}
    
    motif = data.motif if data and data.motif else "Aucun motif fourni"
    
    reservation.refuser(request.user)
    
    # Notification au client
    try:
        NotificationService.notification_reservation_refusee(reservation, motif)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return {
        "success": True,
        "message": f"Reservation #{reservation.id} refusee",
        "reservation_id": reservation.id,
        "statut": "refusee",
        "motif": motif
    }


# ============================================
# ANNULER UNE RESERVATION (Client ou Admin)
# ============================================

@router.put("/{reservation_id}/annuler")
def annuler_reservation(request, reservation_id: int, data: ReservationActionSchema = None):
    """Annuler une reservation (Client ou Admin/Agent/Secretariat)"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and reservation.client != request.user:
        return {"error": "Vous n'etes pas autorise a annuler cette reservation"}
    
    if reservation.statut not in ['en_attente', 'validee']:
        return {"error": f"Cette reservation ne peut pas etre annulee (statut: {reservation.statut})"}
    
    motif = data.motif if data and data.motif else "Annulation par le client"
    
    reservation.annuler(request.user)
    
    return {
        "success": True,
        "message": f"Reservation #{reservation.id} annulee",
        "reservation_id": reservation.id,
        "statut": "annulee",
        "motif": motif
    }


# ============================================
# STATISTIQUES DES RESERVATIONS
# ============================================

@router.get("/stats/global")
def stats_reservations(request):
    """Statistiques des reservations"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    total = Reservation.objects.count()
    en_attente = Reservation.objects.filter(statut='en_attente').count()
    validees = Reservation.objects.filter(statut='validee').count()
    annulees = Reservation.objects.filter(statut='annulee').count()
    refusees = Reservation.objects.filter(statut='refusee').count()
    
    from django.utils import timezone
    from datetime import timedelta
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    mois = Reservation.objects.filter(date_reservation__gte=debut_mois).count()
    
    return {
        "total": total,
        "en_attente": en_attente,
        "validees": validees,
        "annulees": annulees,
        "refusees": refusees,
        "taux_validation": round((validees / total) * 100, 2) if total > 0 else 0,
        "mois_en_cours": mois,
    }


@router.get("/stats/par-mois")
def stats_par_mois(request):
    """Reservations par mois"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', date_reservation) as mois,
                COUNT(*) as total
            FROM reservations_reservation
            GROUP BY DATE_TRUNC('month', date_reservation)
            ORDER BY mois DESC
            LIMIT 12
        """)
        rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append({
            "mois": row[0].strftime("%B %Y") if row[0] else None,
            "total": row[1]
        })
    
    return result


