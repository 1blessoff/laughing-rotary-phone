from ninja import Schema
from typing import Optional
from datetime import datetime

class PaiementSchema(Schema):
    id: int
    reservation_id: int
    reservation_reference: str
    montant: float
    methode: str
    statut: str
    reference_transaction: str
    est_partiel: bool = False
    solde_restant: float = 0
    date_paiement: datetime
    date_validation: Optional[datetime] = None
    valide_par: Optional[int] = None
    valide_par_username: Optional[str] = None
    notes: str = ""
    numero_transaction: str = ""
    operateur: str = ""
    numero_telephone: str = ""

class PaiementCreateSchema(Schema):
    reservation_id: int
    montant: float
    methode: str
    est_partiel: bool = False
    notes: Optional[str] = ""
    numero_transaction: Optional[str] = ""
    operateur: Optional[str] = ""
    numero_telephone: Optional[str] = ""

class PaiementValiderSchema(Schema):
    notes: Optional[str] = ""