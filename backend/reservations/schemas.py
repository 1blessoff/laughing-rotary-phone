from ninja import Schema
from typing import Optional, List
from datetime import date, datetime

class ReservationSchema(Schema):
    id: int
    client_id: int
    client_username: str
    caveau_id: int
    caveau_reference: str
    statut: str
    statut_color: str
    nom_defunt: str
    prenom_defunt: str = ""
    date_naissance: Optional[date] = None
    date_deces: date
    date_enterrement: date
    nom_famille: str = ""
    adresse: str = ""
    telephone: str = ""
    email_contact: str = ""
    notes: str = ""
    besoin_ceremonie: bool = False
    besoin_voiture: bool = False
    date_reservation: datetime
    date_validation: Optional[datetime] = None
    date_annulation: Optional[datetime] = None
    valide_par: Optional[int] = None
    valide_par_username: Optional[str] = None
    facture_pdf: Optional[str] = None
    certificat_pdf: Optional[str] = None

class ReservationCreateSchema(Schema):
    caveau_id: int
    nom_defunt: str
    prenom_defunt: Optional[str] = ""
    date_naissance: Optional[date] = None
    date_deces: date
    date_enterrement: date
    nom_famille: Optional[str] = ""
    adresse: Optional[str] = ""
    telephone: Optional[str] = ""
    email_contact: Optional[str] = ""
    notes: Optional[str] = ""
    besoin_ceremonie: Optional[bool] = False
    besoin_voiture: Optional[bool] = False

class ReservationUpdateSchema(Schema):
    nom_defunt: Optional[str] = None
    prenom_defunt: Optional[str] = None
    date_naissance: Optional[date] = None
    date_deces: Optional[date] = None
    date_enterrement: Optional[date] = None
    nom_famille: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email_contact: Optional[str] = None
    notes: Optional[str] = None
    besoin_ceremonie: Optional[bool] = None
    besoin_voiture: Optional[bool] = None

class ReservationActionSchema(Schema):
    motif: Optional[str] = None

class ReservationFiltreSchema(Schema):
    statut: Optional[str] = None
    client_id: Optional[int] = None
    caveau_id: Optional[int] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    recherche: Optional[str] = None