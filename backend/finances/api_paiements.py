from ninja import Router
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import random
import string
import os

from .models import Paiement
from reservations.models import Reservation
from concessions.models import Concession
from .schemas import PaiementSchema, PaiementCreateSchema, PaiementValiderSchema
from utils.pdf_generator import PDFGenerator
from utils.notifications import NotificationService

User = get_user_model()
router = Router()

# ============================================
# MODE DE PAIEMENT (Configuration)
# ============================================
# MODE SIMULATION (par défaut) : Paiements simulés sans API réelle
# MODE REEL (à activer) : Intégration réelle MTN/Airtel/Virement
# ============================================

PAIEMENT_MODE = "simulation"  # "simulation" ou "reel"

# Pour activer le mode réel, décommentez la ligne ci-dessous :
# PAIEMENT_MODE = "reel"

# ============================================
# CONFIGURATION MTN (Mode Réel - à décommenter)
# ============================================

# MTN_SUBSCRIPTION_KEY = os.getenv("MTN_SUBSCRIPTION_KEY")
# MTN_USER_ID = os.getenv("MTN_USER_ID")
# MTN_API_SECRET = os.getenv("MTN_API_SECRET")
# MTN_ENV = os.getenv("MTN_ENV", "sandbox")
# MTN_BASE_URL = os.getenv("MTN_BASE_URL", "https://sandbox.momodeveloper.mtn.com")

# ============================================
# CONFIGURATION AIRTEL (Mode Réel - à décommenter)
# ============================================

# AIRTEL_CLIENT_ID = os.getenv("AIRTEL_CLIENT_ID")
# AIRTEL_CLIENT_SECRET = os.getenv("AIRTEL_CLIENT_SECRET")
# AIRTEL_BASE_URL = os.getenv("AIRTEL_BASE_URL", "https://openapiuat.airtel.africa")


# ============================================
# FONCTIONS DE SIMULATION
# ============================================

def simuler_paiement_mobile(phone_number, amount, operateur):
    """Simuler un paiement Mobile Money (MTN/Airtel)"""
    reference = f"SIM-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    import time
    time.sleep(0.5)
    
    if random.random() < 0.9:
        return {
            "success": True,
            "reference": reference,
            "message": f"Paiement {operateur} simulé avec succès",
            "statut": "valide"
        }
    else:
        return {
            "success": False,
            "reference": reference,
            "message": f"Paiement {operateur} simulé - Échec",
            "statut": "echoue"
        }


def simuler_virement_bancaire(reference_client, montant):
    """Simuler un virement bancaire"""
    reference = f"VIR-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    import time
    time.sleep(0.5)
    
    return {
        "success": True,
        "reference": reference,
        "message": "Virement bancaire simulé avec succès",
        "statut": "valide"
    }


# ============================================
# PAIEMENTS - CREATION
# ============================================

@router.post("/", response={200: PaiementSchema, 400: dict, 403: dict})
def create_paiement(request, data: PaiementCreateSchema):
    """Enregistrer un paiement (Mode Simulation ou Réel)"""
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}

    reservation = get_object_or_404(Reservation, id=data.reservation_id)

    # FIX : le client doit pouvoir payer SA PROPRE réservation. Avant ce fix,
    # seuls admin/agent/secretariat pouvaient créer un paiement, ce qui
    # empêchait le client de jamais soumettre son propre paiement (403
    # systématique) alors que c'est le flux normal : client paie -> admin
    # valide (voir valider_paiement / refuser_paiement, qui restent
    # réservés au staff, à raison).
    est_staff = request.user.role in ['admin', 'agent', 'secretariat']
    est_proprietaire = reservation.client_id == request.user.id
    if not est_staff and not est_proprietaire:
        return 403, {"error": "Vous ne pouvez payer que vos propres reservations"}

    #VERIFICATION : Empêcher double paiement pour la meme reservation
    if not data.est_partiel:
        existing_paiement = Paiement.objects.filter(
            reservation=reservation,
            statut='valide'
        ).exists()
        
        if existing_paiement:
            return 400, {"error": "Cette reservation a deja ete payee"}

    # FIX : la concession n'existe pas encore a ce stade du flux, et c'est
    # normal. Ordre voulu : reservation validee -> client paie -> admin
    # valide le paiement -> LA la concession est creee automatiquement,
    # une seule fois (voir valider_paiement plus bas). On ne bloque donc
    # plus le paiement sur l'absence de concession. On n'empeche pas non
    # plus un 2e paiement (ex: paiement partiel / solde) une fois la
    # concession deja creee.
    
    reference = f"PAY-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    while Paiement.objects.filter(reference_transaction=reference).exists():
        reference = f"PAY-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    # ============================================
    # MODE REEL (Décommenter pour activer)
    # ============================================
    
    # if PAIEMENT_MODE == "reel":
    #     if data.methode in ["mtn_money", "airtel_money"]:
    #         # Appel aux API réelles
    #         pass
    
    # ============================================
    # MODE SIMULATION (Par défaut)
    # ============================================
    
    if PAIEMENT_MODE == "simulation":
        if data.methode in ["mtn_money", "airtel_money"]:
            operateur = "MTN" if data.methode == "mtn_money" else "Airtel"
            result = simuler_paiement_mobile(
                phone_number=data.numero_telephone or "0612345678",
                amount=data.montant,
                operateur=operateur
            )
            
            paiement = Paiement.objects.create(
                reservation=reservation,
                montant=data.montant,
                methode=data.methode,
                reference_transaction=result.get("reference", reference),
                est_partiel=data.est_partiel,
                notes=data.notes or f"Paiement simulé - {operateur}",
                numero_transaction=data.numero_transaction or result.get("reference", ""),
                operateur=operateur,
                numero_telephone=data.numero_telephone or "",
                statut='en_attente',
            )
                
        elif data.methode == "virement":
            result = simuler_virement_bancaire(
                reference_client=data.numero_transaction or "",
                montant=data.montant
            )
            
            paiement = Paiement.objects.create(
                reservation=reservation,
                montant=data.montant,
                methode=data.methode,
                reference_transaction=result.get("reference", reference),
                est_partiel=data.est_partiel,
                notes=data.notes or "Virement simulé",
                numero_transaction=data.numero_transaction or result.get("reference", ""),
                statut='en_attente',
            )
        else:
            return 400, {"error": "Mode de paiement non supporte"}
    
    return 200, {
        "id": paiement.id,
        "reservation_id": paiement.reservation.id,
        "reservation_reference": f"RES-{paiement.reservation.id}",
        "montant": float(paiement.montant),
        "methode": paiement.methode,
        "statut": paiement.statut,
        "reference_transaction": paiement.reference_transaction,
        "est_partiel": paiement.est_partiel,
        "solde_restant": float(paiement.solde_restant),
        "date_paiement": paiement.date_paiement,
        "date_validation": paiement.date_validation,
        "valide_par": paiement.valide_par.id if paiement.valide_par else None,
        "valide_par_username": paiement.valide_par.username if paiement.valide_par else None,
        "notes": paiement.notes,
        "numero_transaction": paiement.numero_transaction,
        "operateur": paiement.operateur,
        "numero_telephone": paiement.numero_telephone,
    }


# ============================================
# LISTE TOUS LES PAIEMENTS (Admin/Agent)
# ============================================

@router.get("/", response={200: list[PaiementSchema], 403: dict})
def get_all_paiements(request):
    """Liste de tous les paiements (Admin/Agent/Secretariat)"""
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return 403, {"error": "Permission refusee"}
    
    paiements = Paiement.objects.all().order_by('-date_paiement')
    
    result = []
    for p in paiements:
        result.append({
            "id": p.id,
            "reservation_id": p.reservation.id,
            "reservation_reference": f"RES-{p.reservation.id}",
            "client_username": p.reservation.client.username,
            "montant": float(p.montant),
            "methode": p.methode,
            "statut": p.statut,
            "reference_transaction": p.reference_transaction,
            "est_partiel": p.est_partiel,
            "solde_restant": float(p.solde_restant),
            "date_paiement": p.date_paiement,
            "date_validation": p.date_validation,
            "valide_par": p.valide_par.id if p.valide_par else None,
            "valide_par_username": p.valide_par.username if p.valide_par else None,
            "notes": p.notes,
            "numero_transaction": p.numero_transaction,
            "operateur": p.operateur,
            "numero_telephone": p.numero_telephone,
            "facture_pdf": p.facture_pdf.url if p.facture_pdf else None,
        })
    return result


























# ============================================
# VALIDER UN PAIEMENT (avec envoi d'email)
# ============================================

@router.put("/{paiement_id}/valider")
def valider_paiement(request, paiement_id: int, data: PaiementValiderSchema = None):
    """Valider un paiement, generer la facture et envoyer l'email de confirmation"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    paiement = get_object_or_404(Paiement, id=paiement_id)
    
    if paiement.statut != 'en_attente':
        return {"error": f"Ce paiement est deja {paiement.statut}"}
    
    paiement.valider(request.user)
    
    if data and data.notes:
        paiement.notes = data.notes
        paiement.save()

    # ============================================
    # CREATION AUTOMATIQUE DE LA CONCESSION
    # ============================================
    # C'est ICI, une fois le paiement confirme par l'admin, que le contrat
    # de concession est cree pour le client - pas avant. Idempotent : si une
    # concession existe deja (paiement partiel suivant sur la meme
    # reservation), on ne la recree pas.
    reservation = paiement.reservation
    concession = getattr(reservation, 'concession', None)
    concession_nouvellement_creee = concession is None
    if concession is None:
        numero_contrat = f"CONC-{reservation.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        date_debut = datetime.now().date()
        duree_ans = 10  # Valeur par defaut - a exposer cote admin si besoin d'un choix.
        concession = Concession.objects.create(
            reservation=reservation,
            type_concession='temporaire',
            date_debut=date_debut,
            duree_ans=duree_ans,
            date_fin=date_debut + timedelta(days=365 * duree_ans),
            numero_contrat=numero_contrat,
        )
        print(f"Concession {numero_contrat} creee automatiquement pour reservation #{reservation.id}")

        # Generer le contrat PDF et l'envoyer au client (email distinct de
        # la facture : deux documents differents, deux emails differents).
        try:
            contrat_buffer = PDFGenerator.generer_contrat(concession)
            nom_contrat = f"contrat_{concession.numero_contrat}.pdf"
            concession.contrat_pdf.save(nom_contrat, ContentFile(contrat_buffer.getvalue()))
            NotificationService.notification_concession_creee(concession)
        except Exception as e:
            print(f"Erreur generation/envoi contrat concession: {e}")
    
    # Generer la facture PDF
    try:
        pdf_buffer = PDFGenerator.generer_facture(paiement)
        nom_fichier = f"facture_{paiement.reference_transaction}_{datetime.now().strftime('%Y%m%d')}.pdf"
        paiement.facture_pdf.save(nom_fichier, ContentFile(pdf_buffer.getvalue()))
        paiement.facture_generee_le = datetime.now()
        paiement.save()
        
        # Email de confirmation au client, facture en piece jointe.
        # FIX : avant, ce meme email partait DEUX FOIS (une fois via
        # NotificationService.notification_paiement_valide, une fois via un
        # bloc EmailMessage ad-hoc juste en dessous, quasi identique). On ne
        # garde que celui-ci.
        try:
            NotificationService.notification_paiement_valide(paiement)
        except Exception as e:
            print(f"Erreur notification paiement: {e}")

        # Copie de la facture aux administrateurs, pour leurs archives
        try:
            pdf_buffer.seek(0)
            admin_emails = list(
                User.objects.filter(role='admin', email__isnull=False)
                .exclude(email='')
                .values_list('email', flat=True)
            )
            if admin_emails:
                email_admin = EmailMessage(
                    subject=f"[Copie admin] Paiement validé - {paiement.reference_transaction}",
                    body=f"""
Un paiement a été validé par {request.user.username}.

Référence: {paiement.reference_transaction}
Client: {paiement.reservation.client.username}
Réservation: RES-{reservation.id}
Concession: {concession.numero_contrat}
Montant: {paiement.montant:,.0f} FCFA
Méthode: {paiement.get_methode_display()}

Facture en pièce jointe.
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=admin_emails,
                )
                email_admin.attach(nom_fichier, pdf_buffer.getvalue(), 'application/pdf')
                email_admin.send(fail_silently=False)
                print(f"Copie facture envoyée aux admins: {admin_emails}")
        except Exception as e:
            print(f"Erreur envoi copie admin: {e}")
            
    except Exception as e:
        print(f"Erreur generation facture: {e}")
    
    return {
        "success": True,
        "message": f"Paiement {paiement.reference_transaction} valide et facture envoyee",
        "facture_pdf": paiement.facture_pdf.url if paiement.facture_pdf else None,
        "concession": {
            "id": concession.id,
            "numero_contrat": concession.numero_contrat,
            "date_debut": concession.date_debut,
            "date_fin": concession.date_fin,
        },
    }


# ============================================
# REFUSER UN PAIEMENT
# ============================================

@router.put("/{paiement_id}/refuser")
def refuser_paiement(request, paiement_id: int, data: PaiementValiderSchema = None):
    """Refuser un paiement et envoyer une notification"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    paiement = get_object_or_404(Paiement, id=paiement_id)
    
    if paiement.statut != 'en_attente':
        return {"error": f"Ce paiement est deja {paiement.statut}"}
    
    paiement.statut = 'refuse'
    paiement.date_validation = datetime.now()
    paiement.valide_par = request.user
    
    if data and data.notes:
        paiement.notes = data.notes
    paiement.save()
    
    #  Notifier le client du refus
    try:
        client = paiement.reservation.client
        if client.email:
            send_mail(
                subject=f"Paiement refuse - {paiement.reference_transaction}",
                message=f"""
Bonjour {client.username},

Nous vous informons que votre paiement a ete refuse.

Référence: {paiement.reference_transaction}
 Montant: {paiement.montant:,.0f} FCFA
 Date: {datetime.now().strftime('%d/%m/%Y à %H:%M')}
Méthode: {paiement.get_methode_display()}
Motif: {paiement.notes or 'Non specifie'}

Veuillez contacter l'administration pour plus d'informations.

Cordialement,
L'équipe Gestion Funéraire
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=True,
            )
            print(f" Email de refus envoyé à {client.email}")
    except Exception as e:
        print(f" Erreur envoi email refus: {e}")
    
    return {
        "success": True,
        "message": f"Paiement {paiement.reference_transaction} refuse",
        "paiement_id": paiement.id,
        "statut": "refuse"
    }


# ============================================
# TELECHARGER LA FACTURE
# ============================================

@router.get("/{paiement_id}/facture")
def telecharger_facture(request, paiement_id: int):
    """Telecharger la facture PDF"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    paiement = get_object_or_404(Paiement, id=paiement_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and paiement.reservation.client != request.user:
        return {"error": "Vous n'avez pas acces a cette facture"}
    
    if not paiement.facture_pdf:
        return {"error": "La facture n'a pas encore ete generee"}
    
    from django.http import FileResponse
    return FileResponse(paiement.facture_pdf, as_attachment=True, filename=f"facture_{paiement.reference_transaction}.pdf")


# ============================================
# STATISTIQUES DES PAIEMENTS
# ============================================

@router.get("/stats")
def stats_paiements(request):
    """Statistiques des paiements"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    total = Paiement.objects.count()
    en_attente = Paiement.objects.filter(statut='en_attente').count()
    valides = Paiement.objects.filter(statut='valide').count()
    refuses = Paiement.objects.filter(statut='refuse').count()
    echoues = Paiement.objects.filter(statut='echoue').count()
    
    total_montant_valide = sum(p.montant for p in Paiement.objects.filter(statut='valide'))
    total_montant_attente = sum(p.montant for p in Paiement.objects.filter(statut='en_attente'))
    
    return {
        "total_paiements": total,
        "en_attente": en_attente,
        "valides": valides,
        "refuses": refuses,
        "echoues": echoues,
        "total_montant_valide": float(total_montant_valide),
        "total_montant_attente": float(total_montant_attente),
        "par_methode": {
            "airtel_money": Paiement.objects.filter(methode='airtel_money', statut='valide').count(),
            "mtn_money": Paiement.objects.filter(methode='mtn_money', statut='valide').count(),
            "especes": Paiement.objects.filter(methode='especes', statut='valide').count(),
            "virement": Paiement.objects.filter(methode='virement', statut='valide').count(),
        }
    }


# ============================================
# PAIEMENTS PAR RESERVATION
# ============================================

@router.get("/reservation/{reservation_id}", response={200: list[PaiementSchema], 403: dict})
def get_paiements_reservation(request, reservation_id: int):
    """Paiements d'une reservation specifique"""
    # FIX : le schema de reponse declare ne couvrait que list[PaiementSchema].
    # Renvoyer {"error": ...} ici faisait planter la validation Pydantic de
    # Ninja et remontait un 500 au lieu d'un 403 propre pour tout appel non
    # authentifie ou non autorise.
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and reservation.client != request.user:
        return 403, {"error": "Vous n'avez pas acces a cette reservation"}
    
    paiements = Paiement.objects.filter(reservation=reservation).order_by('-date_paiement')
    
    result = []
    for p in paiements:
        result.append({
            "id": p.id,
            "reservation_id": p.reservation.id,
            "reservation_reference": f"RES-{p.reservation.id}",
            "montant": float(p.montant),
            "methode": p.methode,
            "statut": p.statut,
            "reference_transaction": p.reference_transaction,
            "est_partiel": p.est_partiel,
            "solde_restant": float(p.solde_restant),
            "date_paiement": p.date_paiement,
            "date_validation": p.date_validation,
            "valide_par": p.valide_par.id if p.valide_par else None,
            "valide_par_username": p.valide_par.username if p.valide_par else None,
            "notes": p.notes,
            "numero_transaction": p.numero_transaction,
            "operateur": p.operateur,
            "numero_telephone": p.numero_telephone,
            "facture_pdf": p.facture_pdf.url if p.facture_pdf else None,
        })
    return result


# ============================================
# MES PAIEMENTS (client) - filtrage cote serveur
# ============================================
# NOTE : ne jamais faire confiance a un filtrage cote client pour des
# donnees personnelles (nom du defunt, telephone...). Le filtrage doit
# toujours se faire sur request.user cote serveur. Cet endpoint remplace
# la boucle "get_reservations() + filtrer + get_paiements_reservation()
# pour chacune" par UN SEUL appel, deja scope sur l'utilisateur connecte.

@router.get("/mes-paiements", response={200: list[PaiementSchema], 403: dict})
def get_mes_paiements(request):
    """Tous les paiements du client connecte, en un seul appel."""
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}

    if request.user.role in ['admin', 'agent', 'secretariat']:
        paiements = Paiement.objects.all().order_by('-date_paiement')
    else:
        paiements = Paiement.objects.filter(
            reservation__client=request.user
        ).order_by('-date_paiement')

    result = []
    for p in paiements:
        result.append({
            "id": p.id,
            "reservation_id": p.reservation.id,
            "reservation_reference": f"RES-{p.reservation.id}",
            "montant": float(p.montant),
            "methode": p.methode,
            "statut": p.statut,
            "reference_transaction": p.reference_transaction,
            "est_partiel": p.est_partiel,
            "solde_restant": float(p.solde_restant),
            "date_paiement": p.date_paiement,
            "date_validation": p.date_validation,
            "valide_par": p.valide_par.id if p.valide_par else None,
            "valide_par_username": p.valide_par.username if p.valide_par else None,
            "notes": p.notes,
            "numero_transaction": p.numero_transaction,
            "operateur": p.operateur,
            "numero_telephone": p.numero_telephone,
            "facture_pdf": p.facture_pdf.url if p.facture_pdf else None,
        })
    return result
def get_paiement(request, paiement_id: int):
    """Details d'un paiement"""
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie"}
    
    paiement = get_object_or_404(Paiement, id=paiement_id)
    
    if request.user.role not in ['admin', 'agent', 'secretariat'] and paiement.reservation.client != request.user:
        return 403, {"error": "Vous n'avez pas acces a ce paiement"}
    
    return {
        "id": paiement.id,
        "reservation_id": paiement.reservation.id,
        "reservation_reference": f"RES-{paiement.reservation.id}",
        "montant": float(paiement.montant),
        "methode": paiement.methode,
        "statut": paiement.statut,
        "reference_transaction": paiement.reference_transaction,
        "est_partiel": paiement.est_partiel,
        "solde_restant": float(paiement.solde_restant),
        "date_paiement": paiement.date_paiement,
        "date_validation": paiement.date_validation,
        "valide_par": paiement.valide_par.id if paiement.valide_par else None,
        "valide_par_username": paiement.valide_par.username if paiement.valide_par else None,
        "notes": paiement.notes,
        "numero_transaction": paiement.numero_transaction,
        "operateur": paiement.operateur,
        "numero_telephone": paiement.numero_telephone,
        "facture_pdf": paiement.facture_pdf.url if paiement.facture_pdf else None,
    }