from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Q
from typing import List, Optional
from datetime import datetime

from .models import Caveau, CategorieCaveau
from .schemas import (
    CaveauSchema, CaveauCreateSchema, CaveauUpdateSchema,
    CaveauStatutSchema, CaveauFiltreSchema,
    CategorieCaveauSchema, CategorieCaveauCreateSchema
)

router = Router()

# ============================================
# CATEGORIES DE CAVEAUX
# ============================================

@router.post("/categories", response=CategorieCaveauSchema)
def create_categorie(request, data: CategorieCaveauCreateSchema):
    """Creer une nouvelle categorie de caveau"""
    print("=== create_categorie ===")
    print(f"User: {request.user}")
    print(f"Authentifie: {request.user.is_authenticated}")
    
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent']:
        return {"error": "Permission refusee"}
    
    categorie = CategorieCaveau.objects.create(
        nom=data.nom,
        largeur=data.largeur,
        longueur=data.longueur,
        prix_base=data.prix_base
    )
    print(f"Categorie creee: {categorie.nom}")
    print("=" * 50)
    return categorie


@router.get("/categories", response=List[CategorieCaveauSchema])
def list_categories(request):
    """Liste des categories de caveaux"""
    print("=== list_categories ===")
    categories = CategorieCaveau.objects.all().order_by('nom')
    print(f"Nombre de categories: {len(categories)}")
    return categories


@router.get("/categories/{categorie_id}", response=CategorieCaveauSchema)
def get_categorie(request, categorie_id: int):
    """Details d'une categorie"""
    categorie = get_object_or_404(CategorieCaveau, id=categorie_id)
    return categorie


@router.put("/categories/{categorie_id}", response=CategorieCaveauSchema)
def update_categorie(request, categorie_id: int, data: CategorieCaveauCreateSchema):
    """Modifier une categorie"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent']:
        return {"error": "Permission refusee"}
    
    categorie = get_object_or_404(CategorieCaveau, id=categorie_id)
    categorie.nom = data.nom
    categorie.largeur = data.largeur
    categorie.longueur = data.longueur
    categorie.prix_base = data.prix_base
    categorie.save()
    return categorie


@router.delete("/categories/{categorie_id}")
def delete_categorie(request, categorie_id: int):
    """Supprimer une categorie"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role != 'admin':
        return {"error": "Permission refusee"}
    
    categorie = get_object_or_404(CategorieCaveau, id=categorie_id)
    categorie.delete()
    return {"success": True, "message": "Categorie supprimee"}


# ============================================
# CRUD CAVEAUX
# ============================================

@router.post("/", response={200: CaveauSchema, 400: dict, 403: dict})
def create_caveau(request, data: CaveauCreateSchema):
    """Creer un nouveau caveau"""
    print("=" * 60)
    print("=== create_caveau ===")
    print(f"User: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        print(f"Username: {request.user.username}")
        print(f"Role: {request.user.role}")
    else:
        print("User non authentifie")
    print(f"Donnees recues: {data}")
    print("=" * 60)
    
    if not request.user.is_authenticated:
        return 403, {"error": "Non authentifie - Veuillez vous connecter"}
    
    if request.user.role not in ['admin', 'agent']:
        return 403, {"error": f"Permission refusee - Votre role: {request.user.role}"}
    
    # Verifier que la reference est unique
    if Caveau.objects.filter(reference=data.reference).exists():
        return 400, {"error": f"Un caveau avec la reference {data.reference} existe deja"}
    
    # Verifier la categorie
    categorie = None
    if data.categorie_id:
        categorie = get_object_or_404(CategorieCaveau, id=data.categorie_id)
    
    # Creer le caveau
    try:
        caveau = Caveau.objects.create(
            reference=data.reference,
            categorie=categorie,
            section=data.section,
            bloc=data.bloc or "",
            allee=data.allee or "",
            latitude=data.latitude,
            longitude=data.longitude,
            superficie=data.superficie or 0,
            proprietaire_nom=data.proprietaire_nom or "",
            proprietaire_contact=data.proprietaire_contact or "",
            statut='disponible'
        )
        
        # Ajouter a l'historique
        caveau.historique_statut = [{
            'ancien': None,
            'nouveau': 'disponible',
            'utilisateur': str(request.user),
            'date': str(caveau.date_creation)
        }]
        caveau.save()
        
        print(f"Caveau cree avec succes: {caveau.reference}")
        print("=" * 60)
        
        return 200, {
            "id": caveau.id,
            "reference": caveau.reference,
            "categorie_id": caveau.categorie.id if caveau.categorie else None,
            "categorie_nom": caveau.categorie.nom if caveau.categorie else None,
            "statut": caveau.statut,
            "latitude": caveau.latitude,
            "longitude": caveau.longitude,
            "section": caveau.section,
            "bloc": caveau.bloc,
            "allee": caveau.allee,
            "superficie": float(caveau.superficie),
            "proprietaire_nom": caveau.proprietaire_nom,
            "proprietaire_contact": caveau.proprietaire_contact,
            "date_creation": caveau.date_creation,
            "date_modification": caveau.date_modification,
            "historique_statut": caveau.historique_statut,
            "statut_color": caveau.get_statut_color(),
            "est_disponible": caveau.est_disponible,
        }
    except Exception as e:
        print(f"❌ Erreur lors de la creation: {e}")
        return 400, {"error": str(e)}


@router.get("/", response=List[CaveauSchema])
def list_caveaux(request, filters: CaveauFiltreSchema = Query(...)):
    """Liste des caveaux avec filtres"""
    print("=== list_caveaux ===")
    print(f"User: {request.user}")
    print(f"Filtres: {filters}")
    
    caveaux = Caveau.objects.all().order_by('section', 'reference')
    
    # Filtres
    if filters.section:
        caveaux = caveaux.filter(section=filters.section)
    
    if filters.bloc:
        caveaux = caveaux.filter(bloc=filters.bloc)
    
    if filters.statut:
        caveaux = caveaux.filter(statut=filters.statut)
    
    if filters.disponibles_seulement:
        caveaux = caveaux.filter(statut='disponible')
    
    if filters.recherche:
        caveaux = caveaux.filter(
            Q(reference__icontains=filters.recherche) |
            Q(section__icontains=filters.recherche) |
            Q(bloc__icontains=filters.recherche)
        )
    
    print(f"Nombre de caveaux trouves: {len(caveaux)}")
    
    result = []
    for c in caveaux:
        # Récupérer le prix depuis la catégorie
        prix_base = c.categorie.prix_base if c.categorie else 0
        result.append({
            "id": c.id,
            "reference": c.reference,
            "categorie_id": c.categorie.id if c.categorie else None,
            "categorie_nom": c.categorie.nom if c.categorie else None,
            "prix_base": float(prix_base), 
            "statut": c.statut,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "section": c.section,
            "bloc": c.bloc,
            "allee": c.allee,
            "superficie": float(c.superficie),
            "proprietaire_nom": c.proprietaire_nom,
            "proprietaire_contact": c.proprietaire_contact,
            "date_creation": c.date_creation,
            "date_modification": c.date_modification,
            "historique_statut": c.historique_statut,
            "statut_color": c.get_statut_color(),
            "est_disponible": c.est_disponible,
        })
        
    return result


@router.get("/{caveau_id}", response=CaveauSchema)
def get_caveau(request, caveau_id: int):
    """Details d'un caveau"""
    print(f"=== get_caveau id={caveau_id} ===")
    caveau = get_object_or_404(Caveau, id=caveau_id)

    prix_base = float(caveau.categorie.prix_base) if caveau.categorie else 0 

    return {
        "id": caveau.id,
        "reference": caveau.reference,
        "categorie_id": caveau.categorie.id if caveau.categorie else None,
        "categorie_nom": caveau.categorie.nom if caveau.categorie else None,
        "prix_base": prix_base,
        "statut": caveau.statut,
        "latitude": caveau.latitude,
        "longitude": caveau.longitude,
        "section": caveau.section,
        "bloc": caveau.bloc,
        "allee": caveau.allee,
        "superficie": float(caveau.superficie),
        "proprietaire_nom": caveau.proprietaire_nom,
        "proprietaire_contact": caveau.proprietaire_contact,
        "date_creation": caveau.date_creation,
        "date_modification": caveau.date_modification,
        "historique_statut": caveau.historique_statut,
        "statut_color": caveau.get_statut_color(),
        "est_disponible": caveau.est_disponible,
    }


@router.put("/{caveau_id}", response=CaveauSchema)
def update_caveau(request, caveau_id: int, data: CaveauUpdateSchema):
    """Modifier un caveau"""
    print(f"=== update_caveau id={caveau_id} ===")
    print(f"User: {request.user}")
    
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role not in ['admin', 'agent']:
        return {"error": "Permission refusee"}
    
    caveau = get_object_or_404(Caveau, id=caveau_id)
    
    # Mettre a jour les champs
    if data.reference is not None:
        if Caveau.objects.filter(reference=data.reference).exclude(id=caveau.id).exists():
            return {"error": f"La reference {data.reference} est deja utilisee"}
        caveau.reference = data.reference
    
    if data.categorie_id is not None:
        caveau.categorie = get_object_or_404(CategorieCaveau, id=data.categorie_id)
    
    if data.section is not None:
        caveau.section = data.section
    
    if data.bloc is not None:
        caveau.bloc = data.bloc
    
    if data.allee is not None:
        caveau.allee = data.allee
    
    if data.latitude is not None:
        caveau.latitude = data.latitude
    
    if data.longitude is not None:
        caveau.longitude = data.longitude
    
    if data.superficie is not None:
        caveau.superficie = data.superficie
    
    if data.proprietaire_nom is not None:
        caveau.proprietaire_nom = data.proprietaire_nom
    
    if data.proprietaire_contact is not None:
        caveau.proprietaire_contact = data.proprietaire_contact
    
    if data.statut is not None and data.statut in dict(Caveau.STATUT_CHOICES):
        caveau.changer_statut(data.statut, request.user)
    
    caveau.save()
    print(f"Caveau modifie: {caveau.reference}")
    return caveau


@router.delete("/{caveau_id}")
def delete_caveau(request, caveau_id: int):
    """Supprimer un caveau"""
    print(f"=== delete_caveau id={caveau_id} ===")
    print(f"User: {request.user}")
    
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    if request.user.role != 'admin':
        return {"error": "Permission refusee"}
    
    caveau = get_object_or_404(Caveau, id=caveau_id)
    reference = caveau.reference
    caveau.delete()
    print(f"Caveau supprime: {reference}")
    return {"success": True, "message": f"Caveau {reference} supprime"}


# ============================================
# GESTION DES STATUTS
# ============================================

@router.put("/{caveau_id}/statut")
def changer_statut_caveau(request, caveau_id: int, data: CaveauStatutSchema):
    """Changer le statut d'un caveau"""
    print(f"=== changer_statut_caveau id={caveau_id} ===")
    print(f"User: {request.user}")
    print(f"Nouveau statut: {data.nouveau_statut}")
    
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    caveau = get_object_or_404(Caveau, id=caveau_id)
    
    if data.nouveau_statut not in dict(Caveau.STATUT_CHOICES):
        return {"error": "Statut invalide"}
    
    if request.user.role not in ['admin', 'agent', 'secretariat']:
        return {"error": "Permission refusee"}
    
    ancien_statut = caveau.statut
    caveau.changer_statut(data.nouveau_statut, request.user)
    
    print(f"Statut change: {ancien_statut} -> {data.nouveau_statut}")
    return {
        "success": True,
        "message": f"Statut change de {ancien_statut} a {data.nouveau_statut}",
        "ancien_statut": ancien_statut,
        "nouveau_statut": data.nouveau_statut,
        "historique": caveau.historique_statut
    }


@router.get("/{caveau_id}/historique")
def get_historique_caveau(request, caveau_id: int):
    """Obtenir l'historique des statuts d'un caveau"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    caveau = get_object_or_404(Caveau, id=caveau_id)
    return {
        "caveau": caveau.reference,
        "historique": caveau.historique_statut,
        "statut_actuel": caveau.statut
    }


# ============================================
# STATISTIQUES DES CAVEAUX
# ============================================

@router.get("/stats/sections")
def stats_par_section(request):
    """Statistiques des caveaux par section"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    sections = Caveau.objects.values('section').distinct()
    result = []
    
    for s in sections:
        section = s['section']
        total = Caveau.objects.filter(section=section).count()
        disponibles = Caveau.objects.filter(section=section, statut='disponible').count()
        reserves = Caveau.objects.filter(section=section, statut='reserve').count()
        occupes = Caveau.objects.filter(section=section, statut='occupe').count()
        non_exploitables = Caveau.objects.filter(section=section, statut='non_exploitable').count()
        
        result.append({
            "section": section,
            "total": total,
            "disponibles": disponibles,
            "reserves": reserves,
            "occupes": occupes,
            "non_exploitables": non_exploitables,
            "taux_occupation": round((occupes / total) * 100, 2) if total > 0 else 0,
            "taux_disponibilite": round((disponibles / total) * 100, 2) if total > 0 else 0,
        })
    
    return result


@router.get("/stats/global")
def stats_global(request):
    """Statistiques globales des caveaux"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    total = Caveau.objects.count()
    disponibles = Caveau.objects.filter(statut='disponible').count()
    reserves = Caveau.objects.filter(statut='reserve').count()
    occupes = Caveau.objects.filter(statut='occupe').count()
    non_exploitables = Caveau.objects.filter(statut='non_exploitable').count()
    
    return {
        "total": total,
        "disponibles": disponibles,
        "reserves": reserves,
        "occupes": occupes,
        "non_exploitables": non_exploitables,
        "taux_occupation": round((occupes / total) * 100, 2) if total > 0 else 0,
        "taux_disponibilite": round((disponibles / total) * 100, 2) if total > 0 else 0,
        "taux_reserve": round((reserves / total) * 100, 2) if total > 0 else 0,
    }


@router.get("/sections")
def list_sections(request):
    """Liste des sections disponibles"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    sections = Caveau.objects.values_list('section', flat=True).distinct().order_by('section')
    return {"sections": list(sections)}


@router.get("/blocs/{section}")
def list_blocs(request, section: str):
    """Liste des blocs dans une section"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifie"}
    
    blocs = Caveau.objects.filter(section=section).values_list('bloc', flat=True).distinct().order_by('bloc')
    return {"section": section, "blocs": list(blocs)}