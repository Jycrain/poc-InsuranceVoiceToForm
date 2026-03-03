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
