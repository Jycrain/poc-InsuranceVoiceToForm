"""Tests unitaires — modèles Pydantic."""
import pytest
from datetime import date

from src.core.models import FormulaireExpertise, TypeSinistre


def test_formulaire_vide():
    f = FormulaireExpertise()
    assert f.date_sinistre is None
    assert f.tiers_implique is False


def test_formulaire_complet():
    f = FormulaireExpertise(
        date_sinistre=date(2026, 2, 24),
        type_sinistre=TypeSinistre.DEGAT_DES_EAUX,
        localisation="Cuisine",
        tiers_implique=False,
        description_courte="Fuite lave-vaisselle en cuisine.",
    )
    assert f.type_sinistre == "Dégât des eaux"
    assert f.localisation == "Cuisine"


def test_formulaire_serialisation():
    f = FormulaireExpertise(
        date_sinistre=date(2026, 2, 24),
        type_sinistre=TypeSinistre.INCENDIE,
    )
    data = f.model_dump()
    assert data["type_sinistre"] == "Incendie"
    assert data["date_sinistre"] == date(2026, 2, 24)


def test_type_sinistre_enum_values():
    assert TypeSinistre.DEGAT_DES_EAUX.value == "Dégât des eaux"
    assert TypeSinistre.VOL.value == "Vol"
    assert TypeSinistre.BRIS_DE_GLACE.value == "Bris de glace"
