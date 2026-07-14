from ninja import Schema
from typing import Optional
from datetime import datetime

class CategorieCaveauSchema(Schema):
    id: Optional[int] = None
    nom: str
    largeur: float
    longueur: float
    prix_base: float

class CategorieCaveauCreateSchema(Schema):
    nom: str
    largeur: float
    longueur: float
    prix_base: float

class CaveauSchema(Schema):
    id: int
    reference: str
    categorie_id: Optional[int] = None
    categorie_nom: Optional[str] = None
    prix_base: Optional[float] = 0
    statut: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    section: str
    bloc: str = ""
    allee: str = ""
    superficie: float = 0
    proprietaire_nom: str = ""
    proprietaire_contact: str = ""
    date_creation: datetime
    date_modification: datetime
    historique_statut: list = []
    statut_color: str = "gray"
    est_disponible: bool = True

class CaveauCreateSchema(Schema):
    reference: str
    categorie_id: Optional[int] = None
    section: str
    bloc: Optional[str] = ""
    allee: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    superficie: float = 0
    proprietaire_nom: Optional[str] = ""
    proprietaire_contact: Optional[str] = ""

class CaveauUpdateSchema(Schema):
    reference: Optional[str] = None
    categorie_id: Optional[int] = None
    section: Optional[str] = None
    bloc: Optional[str] = None
    allee: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    superficie: Optional[float] = None
    proprietaire_nom: Optional[str] = None
    proprietaire_contact: Optional[str] = None
    statut: Optional[str] = None

class CaveauStatutSchema(Schema):
    nouveau_statut: str
    motif: Optional[str] = None

class CaveauFiltreSchema(Schema):
    section: Optional[str] = None
    bloc: Optional[str] = None
    statut: Optional[str] = None
    recherche: Optional[str] = None
    disponibles_seulement: Optional[bool] = False