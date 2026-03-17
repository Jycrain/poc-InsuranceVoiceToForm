"""
Modèles Pydantic — schémas de données du formulaire d'expertise sinistre.
Pas de BDD pour la V1 : tout transite via ces modèles validés.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TypeSinistre(str, Enum):
    DEGAT_DES_EAUX = "Dégât des eaux"
    INCENDIE = "Incendie"
    VOL = "Vol"
    BRIS_DE_GLACE = "Bris de glace"
    AUTRE = "Autre"


class FormulaireExpertise(BaseModel):
    """
    Représente le formulaire pré-rempli à destination du téléconseiller.
    Tous les champs sont optionnels : le système remplit ce qu'il peut extraire.
    """

    date_sinistre: Optional[date] = Field(
        None,
        description="Date du sinistre mentionnée par l'assuré.",
        examples=["2026-02-24"],
    )
    type_sinistre: Optional[TypeSinistre] = Field(
        None,
        description="Catégorie du sinistre.",
        examples=["Dégât des eaux"],
    )
    localisation: Optional[str] = Field(
        None,
        description="Pièce concernée ou adresse.",
        examples=["Cuisine"],
    )
    tiers_implique: bool = Field(
        False,
        description="Présence d'un tiers responsable ou victime.",
    )
    description_courte: Optional[str] = Field(
        None,
        description="Résumé synthétique du dommage (≤ 200 caractères).",
    )
    transcription_brute: Optional[str] = Field(
        None,
        description="Texte intégral retourné par le moteur STT.",
    )

    model_config = {"use_enum_values": True}


# ---------------------------------------------------------------------------
# Modèles d'extraction LLM — couvrent les 6 sections du dossier
# ---------------------------------------------------------------------------


class TiersExtraction(BaseModel):
    nom: Optional[str] = None
    role: Optional[str] = None
    convoque: Optional[bool] = Field(None, description="Le tiers a-t-il été convoqué ?")
    present: Optional[bool] = Field(None, description="Le tiers était-il présent ?")


class IntervenantExtraction(BaseModel):
    nom_assure: Optional[str] = Field(None, description="Nom complet de l'assuré")
    qualite_assure: Optional[str] = Field(
        None, description="Propriétaire | Locataire | Copropriétaire | Gérant | Autre"
    )
    convoque_assure: Optional[bool] = Field(None, description="L'assuré a-t-il été convoqué ?")
    present_assure: Optional[bool] = Field(None, description="L'assuré était-il présent ?")
    date_rdv: Optional[str] = Field(None, description="Date du RDV (YYYY-MM-DD)")
    heure_debut: Optional[str] = Field(None, description="Heure début (HH:MM)")
    heure_fin: Optional[str] = Field(None, description="Heure fin (HH:MM)")
    tiers: list[TiersExtraction] = Field(default_factory=list)


class ContratExtraction(BaseModel):
    type: Optional[str] = Field(None, description="Particulier | Professionnel")
    description_risque: Optional[str] = None
    conformite: Optional[str] = Field(None, description="Oui | Non | Non vérifié")
    conformite_description: Optional[str] = None


class SinistreExtraction(BaseModel):
    date: Optional[str] = Field(None, description="Date du sinistre (YYYY-MM-DD)")
    type: Optional[str] = Field(
        None,
        description="Dégât des eaux | Incendie | Vol | Bris de glace | Autre",
    )
    localisation: Optional[str] = None
    tiers_implique: Optional[bool] = None
    circonstances: Optional[str] = None
    causes: Optional[str] = None
    dommages_desc: Optional[str] = None


class DommageItem(BaseModel):
    designation: str
    categorie: Optional[str] = Field(
        None, description="immobilier | embellissement | mobilier | autres"
    )
    qte: int = 1
    unite: str = "U"
    pu_ht: Optional[float] = None
    vet: Optional[int] = Field(None, description="Vétusté en % (0-100)")


class DommagesExtraction(BaseModel):
    items: list[DommageItem] = Field(default_factory=list)


class IndemnisationExtraction(BaseModel):
    franchise: Optional[float] = Field(None, description="Montant de la franchise en euros")


class ConclusionExtraction(BaseModel):
    responsabilites: Optional[str] = None
    convention: Optional[str] = Field(
        None,
        description="IRSI T1 | IRSI T2 | CIDE-COP | CIPIEC | Cumul Ass. | Sans objet | Autre",
    )
    garantie_acquise: Optional[str] = Field(None, description="Oui | Non")
    avec_reserve: Optional[bool] = None
    garantie_applicable: Optional[str] = None
    beneficiaire: Optional[str] = None
    garantie_description: Optional[str] = None
    conclusion_expert: Optional[str] = None
    recours: list[str] = Field(default_factory=list, description="Actions de recours engagées")


class DossierExtraction(BaseModel):
    """Extraction complète couvrant les 6 sections du dossier d'expertise."""

    intervenants: Optional[IntervenantExtraction] = None
    contrat: Optional[ContratExtraction] = None
    sinistre: Optional[SinistreExtraction] = None
    dommages: Optional[DommagesExtraction] = None
    indemnisation: Optional[IndemnisationExtraction] = None
    conclusion: Optional[ConclusionExtraction] = None
    notes: Optional[str] = Field(None, description="Notes libres pour le dossier")
    statut: Optional[str] = Field(
        None, description="À traiter | En cours | Clôturé"
    )
