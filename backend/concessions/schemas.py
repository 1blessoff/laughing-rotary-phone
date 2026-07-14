from ninja import Schema
from typing import Optional, List
from datetime import date, datetime

class ConcessionSchema(Schema):
    id: int
    reservation_id: int
    reservation_reference: str
    type_concession: str
    date_debut: date
    duree_ans: int
    date_fin: Optional[date] = None
    actif: bool
    renouvelable: bool
    date_renouvellement: Optional[date] = None
    numero_contrat: Optional[str] = None
    est_expiree: bool = False
    jours_restants: Optional[int] = None

class ConcessionCreateSchema(Schema):
    reservation_id: int
    type_concession: str = "temporaire"
    date_debut: date
    duree_ans: int = 10

class ConcessionRenouvelerSchema(Schema):
    duree_ans: Optional[int] = None

class ExhumationSchema(Schema):
    id: int
    concession_id: int
    demandeur_id: int
    demandeur_username: str
    statut: str
    motif: str
    date_demande: datetime
    date_approbation: Optional[datetime] = None
    date_realisation: Optional[datetime] = None
    approuve_par: Optional[int] = None
    approuve_par_username: Optional[str] = None
    autorisation_pdf: Optional[str] = None
    proces_verbal_pdf: Optional[str] = None
    notes: str = ""

class ExhumationCreateSchema(Schema):
    concession_id: int
    motif: str
    notes: Optional[str] = ""

class ExhumationActionSchema(Schema):
    motif: Optional[str] = None
    notes: Optional[str] = None