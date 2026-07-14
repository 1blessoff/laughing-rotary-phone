from ninja import Router
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import random
import string

from .models import Concession, Exhumation
from reservations.models import Reservation
from .schemas import (
    ConcessionSchema, ConcessionCreateSchema, ConcessionRenouvelerSchema,
    ExhumationSchema, ExhumationCreateSchema, ExhumationActionSchema
)
from utils.notifications import NotificationService  # ← AJOUT

User = get_user_model()
router = Router()

# ============================================
# CONCESSIONS
# ============================================

@router.post("/", response={200: ConcessionSchema, 400: dict, 403: dict})
def create_concession(request, data: ConcessionCreateSchema):
    """Creer une concession pour une reservation validee"""
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return 403, {"error": "Permission refusee"}
    
    reservation = get_object_or_404(Reservation, id=data.reservation_id)
    
    if reservation.statut != 'validee':
        return 400, {"error": "La reservation doit etre validee avant de creer une concession"}
    
    if hasattr(reservation, 'concession'):
        return 400, {"error": "Une concession existe deja pour cette reservation"}
    
    # Calculer la date de fin
    date_fin = None
    if data.type_concession == 'temporaire' and data.duree_ans > 0:
        date_fin = data.date_debut + timedelta(days=365 * data.duree_ans)
    
    # Generer un numero de contrat
    numero_contrat = f"CON-{datetime.now().year}-{random.randint(1000, 9999)}"
    while Concession.objects.filter(numero_contrat=numero_contrat).exists():
        numero_contrat = f"CON-{datetime.now().year}-{random.randint(1000, 9999)}"
    
    concession = Concession.objects.create(
        reservation=reservation,
        type_concession=data.type_concession,
        date_debut=data.date_debut,
        duree_ans=data.duree_ans,
        date_fin=date_fin,
        numero_contrat=numero_contrat,
        renouvelable=(data.type_concession == 'temporaire'),
    )
    
    # Notification au client
    try:
        NotificationService.notification_concession_creee(concession)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return 200, {
        "id": concession.id,
        "reservation_id": concession.reservation.id,
        "reservation_reference": f"RES-{concession.reservation.id}",
        "type_concession": concession.type_concession,
        "date_debut": concession.date_debut,
        "duree_ans": concession.duree_ans,
        "date_fin": concession.date_fin,
        "actif": concession.actif,
        "renouvelable": concession.renouvelable,
        "date_renouvellement": concession.date_renouvellement,
        "numero_contrat": concession.numero_contrat,
        "est_expiree": concession.est_expiree(),
        "jours_restants": concession.jours_restants(),
    }


@router.get("/", response=list[ConcessionSchema])
def list_concessions(request):
    """Liste des concessions"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role in ['admin', 'agent', 'secretariat']:
        concessions = Concession.objects.all().order_by('-date_creation')
    else:
        concessions = Concession.objects.filter(reservation__client=request.user).order_by('-date_creation')
    
    result = []
    for c in concessions:
        result.append({
            "id": c.id,
            "reservation_id": c.reservation.id,
            "reservation_reference": f"RES-{c.reservation.id}",
            "type_concession": c.type_concession,
            "date_debut": c.date_debut,
            "duree_ans": c.duree_ans,
            "date_fin": c.date_fin,
            "actif": c.actif,
            "renouvelable": c.renouvelable,
            "date_renouvellement": c.date_renouvellement,
            "numero_contrat": c.numero_contrat,
            "est_expiree": c.est_expiree(),
            "jours_restants": c.jours_restants(),
        })
    return result


@router.get("/{concession_id}", response=ConcessionSchema)
def get_concession(request, concession_id: int):
    """Details d'une concession"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    concession = get_object_or_404(Concession, id=concession_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and concession.reservation.client != request.user:
        return {"error": "Vous n'avez pas acces a cette concession"}
    
    return {
        "id": concession.id,
        "reservation_id": concession.reservation.id,
        "reservation_reference": f"RES-{concession.reservation.id}",
        "type_concession": concession.type_concession,
        "date_debut": concession.date_debut,
        "duree_ans": concession.duree_ans,
        "date_fin": concession.date_fin,
        "actif": concession.actif,
        "renouvelable": concession.renouvelable,
        "date_renouvellement": concession.date_renouvellement,
        "numero_contrat": concession.numero_contrat,
        "est_expiree": concession.est_expiree(),
        "jours_restants": concession.jours_restants(),
    }


@router.put("/{concession_id}/renouveler")
def renouveler_concession(request, concession_id: int, data: ConcessionRenouvelerSchema):
    """Renouveler une concession"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    concession = get_object_or_404(Concession, id=concession_id)
    
    if concession.type_concession == 'perpetuelle':
        return {"error": "Les concessions perpetuelles ne peuvent pas etre renouvelees"}
    
    if not concession.renouvelable:
        return {"error": "Cette concession n'est pas renouvelable"}
    
    result = concession.renouveler(data.duree_ans)
    
    if isinstance(result, dict) and 'error' in result:
        return result
    
    # Notification de renouvellement
    try:
        NotificationService.notification_concession_renouvelee(concession)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return {
        "success": True,
        "message": f"Concession renouvelee jusqu'au {concession.date_fin}",
        "date_fin": concession.date_fin,
    }


@router.get("/expirations/prochaines")
def concessions_expirant(request):
    """Liste des concessions qui vont expirer dans les 30 jours"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    today = datetime.now().date()
    limite = today + timedelta(days=30)
    
    concessions = Concession.objects.filter(
        date_fin__gte=today,
        date_fin__lte=limite,
        actif=True,
        type_concession='temporaire'
    ).order_by('date_fin')
    
    result = []
    for c in concessions:
        result.append({
            "id": c.id,
            "numero_contrat": c.numero_contrat,
            "reservation_id": c.reservation.id,
            "client": c.reservation.client.username,
            "defunt": c.reservation.nom_defunt,
            "date_fin": c.date_fin,
            "jours_restants": c.jours_restants(),
        })
    
    return result


# ============================================
# EXHUMATIONS
# ============================================

@router.post("/exhumations", response=ExhumationSchema)
def create_exhumation(request, data: ExhumationCreateSchema):
    """Creer une demande d'exhumation"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    concession = get_object_or_404(Concession, id=data.concession_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and concession.reservation.client != request.user:
        return {"error": "Vous n'etes pas autorise"}
    
    if Exhumation.objects.filter(concession=concession, statut__in=['demande', 'approuvee']).exists():
        return {"error": "Une demande d'exhumation est deja en cours pour cette concession"}
    
    exhumation = Exhumation.objects.create(
        concession=concession,
        demandeur=request.user,
        motif=data.motif,
        notes=data.notes or "",
    )
    
    # Notification aux admins
    try:
        NotificationService.notification_exhumation_demande(exhumation)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return {
        "id": exhumation.id,
        "concession_id": exhumation.concession.id,
        "demandeur_id": exhumation.demandeur.id,
        "demandeur_username": exhumation.demandeur.username,
        "statut": exhumation.statut,
        "motif": exhumation.motif,
        "date_demande": exhumation.date_demande,
        "date_approbation": exhumation.date_approbation,
        "date_realisation": exhumation.date_realisation,
        "approuve_par": exhumation.approuve_par.id if exhumation.approuve_par else None,
        "approuve_par_username": exhumation.approuve_par.username if exhumation.approuve_par else None,
        "autorisation_pdf": exhumation.autorisation_pdf.url if exhumation.autorisation_pdf else None,
        "proces_verbal_pdf": exhumation.proces_verbal_pdf.url if exhumation.proces_verbal_pdf else None,
        "notes": exhumation.notes,
    }


@router.get("/exhumations", response=list[ExhumationSchema])
def list_exhumations(request):
    """Liste des exhumations"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role in ['admin', 'agent', 'secretariat']:
        exhumations = Exhumation.objects.all().order_by('-date_demande')
    else:
        exhumations = Exhumation.objects.filter(demandeur=request.user).order_by('-date_demande')
    
    result = []
    for e in exhumations:
        result.append({
            "id": e.id,
            "concession_id": e.concession.id,
            "demandeur_id": e.demandeur.id,
            "demandeur_username": e.demandeur.username,
            "statut": e.statut,
            "motif": e.motif,
            "date_demande": e.date_demande,
            "date_approbation": e.date_approbation,
            "date_realisation": e.date_realisation,
            "approuve_par": e.approuve_par.id if e.approuve_par else None,
            "approuve_par_username": e.approuve_par.username if e.approuve_par else None,
            "autorisation_pdf": e.autorisation_pdf.url if e.autorisation_pdf else None,
            "proces_verbal_pdf": e.proces_verbal_pdf.url if e.proces_verbal_pdf else None,
            "notes": e.notes,
        })
    return result


@router.put("/exhumations/{exhumation_id}/approuver")
def approuver_exhumation(request, exhumation_id: int, data: ExhumationActionSchema = None):
    """Approuver une demande d'exhumation"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    exhumation = get_object_or_404(Exhumation, id=exhumation_id)
    
    if exhumation.statut != 'demande':
        return {"error": f"Cette demande est deja {exhumation.statut}"}
    
    exhumation.approuver(request.user)
    
    # Notification au demandeur
    try:
        NotificationService.notification_exhumation_approuvee(exhumation)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return {"success": True, "message": "Demande d'exhumation approuvee"}


@router.put("/exhumations/{exhumation_id}/realiser")
def realiser_exhumation(request, exhumation_id: int):
    """Marquer une exhumation comme realisee"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent']:
        return {"error": "Permission refusee"}
    
    exhumation = get_object_or_404(Exhumation, id=exhumation_id)
    
    if exhumation.statut != 'approuvee':
        return {"error": "Cette demande doit etre approuvee avant d'etre realisee"}
    
    exhumation.realiser()
    
    return {"success": True, "message": "Exhumation realisee avec succes"}


@router.put("/exhumations/{exhumation_id}/refuser")
def refuser_exhumation(request, exhumation_id: int, data: ExhumationActionSchema = None):
    """Refuser une demande d'exhumation"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    exhumation = get_object_or_404(Exhumation, id=exhumation_id)
    
    if exhumation.statut != 'demande':
        return {"error": f"Cette demande est deja {exhumation.statut}"}
    
    motif = data.motif if data else "Aucun motif fourni"
    exhumation.refuser(request.user, motif)
    
    # Notification au demandeur
    try:
        NotificationService.notification_exhumation_refusee(exhumation, motif)
    except Exception as e:
        print(f"Erreur notification: {e}")
    
    return {"success": True, "message": "Demande d'exhumation refusee", "motif": motif}


@router.get("/{concession_id}/contrat")
def telecharger_contrat(request, concession_id: int):
    """Telecharger le contrat PDF"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    concession = get_object_or_404(Concession, id=concession_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and concession.reservation.client != request.user:
        return {"error": "Vous n'avez pas acces a ce contrat"}
    
    if not concession.contrat_pdf:
        try:
            from utils.pdf_generator import PDFGenerator
            from django.core.files.base import ContentFile
            
            pdf_buffer = PDFGenerator.generer_contrat(concession)
            nom_fichier = f"contrat_{concession.numero_contrat}_{datetime.now().strftime('%Y%m%d')}.pdf"
            concession.contrat_pdf.save(nom_fichier, ContentFile(pdf_buffer.getvalue()))
            concession.save()
            
            # Notification avec contrat en pièce jointe
            try:
                NotificationService.notification_contrat_genere(concession)
            except Exception as e:
                print(f"Erreur notification: {e}")
                
        except Exception as e:
            print(f"Erreur generation contrat: {e}")
            return {"error": "Erreur lors de la generation du contrat"}
    
    if not concession.contrat_pdf:
        return {"error": "Le contrat n'a pas encore ete generee"}
    
    from django.http import FileResponse
    return FileResponse(concession.contrat_pdf, as_attachment=True, filename=f"contrat_{concession.numero_contrat}.pdf")