"""
Tests unitaires pour l'extracteur LLM (avec provider mocké — aucun appel réseau).

Architecture double-passe : le mock doit retourner la même réponse pour les deux
appels séquentiels (Passe A et Passe B). Le merge dans l'extracteur reconstitue
le résultat final.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src.core.interfaces import LLMProviderInterface
from src.core.models import DossierExtraction
from src.providers.llm_extractor import LLMDossierExtractor
from tests.fixtures.transcripts import (
    INCENDIE_MULTI_SECTION,
    MINIMAL_INFO,
    NOISY_CONVERSATION,
    SIMPLE_DEGAT_EAUX,
    VOL_AVEC_INTERRUPTIONS,
)


# ---------------------------------------------------------------------------
# Mock LLM Provider — enregistre les deux appels (Passe A + Passe B)
# ---------------------------------------------------------------------------


class MockLLMProvider(LLMProviderInterface):
    """Provider factice : retourne une réponse JSON pré-configurée."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    async def complete_json(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict[str, Any]:
        self.calls.append({
            "system_prompt": system_prompt,
            "user_message": user_message,
        })
        return self.response

    @property
    def last_system_prompt(self) -> str:
        return self.calls[-1]["system_prompt"] if self.calls else ""

    @property
    def last_user_message(self) -> str:
        return self.calls[-1]["user_message"] if self.calls else ""

    @property
    def all_system_prompts(self) -> str:
        return " ".join(c["system_prompt"] for c in self.calls)

    @property
    def all_user_messages(self) -> str:
        return " ".join(c["user_message"] for c in self.calls)


# ---------------------------------------------------------------------------
# Tests de base
# ---------------------------------------------------------------------------


class TestLLMDossierExtractorBasics:
    """Tests de base : wiring, structure, backward compat."""

    def test_extract_dossier_returns_model(self):
        mock = MockLLMProvider({"sinistre": {"type": "Dégât des eaux"}})
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier(SIMPLE_DEGAT_EAUX))
        assert isinstance(result, DossierExtraction)
        assert result.sinistre is not None
        assert result.sinistre.type == "Dégât des eaux"

    def test_empty_response_gives_empty_extraction(self):
        mock = MockLLMProvider({})
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier(MINIMAL_INFO))
        assert isinstance(result, DossierExtraction)
        assert result.sinistre is None

    def test_transcript_forwarded_to_provider(self):
        mock = MockLLMProvider({})
        extractor = LLMDossierExtractor(mock)
        asyncio.run(extractor.extract_dossier("Texte de test"))
        # Les deux passes reçoivent la transcription
        assert all("Texte de test" in c["user_message"] for c in mock.calls)

    def test_system_prompt_contains_insurance_keywords(self):
        mock = MockLLMProvider({})
        extractor = LLMDossierExtractor(mock)
        asyncio.run(extractor.extract_dossier("test"))
        combined = mock.all_system_prompts.lower()
        assert "sinistre" in combined
        assert "irsi" in combined
        assert "json" in combined

    def test_double_pass_makes_two_calls(self):
        mock = MockLLMProvider({})
        extractor = LLMDossierExtractor(mock)
        asyncio.run(extractor.extract_dossier("test"))
        assert len(mock.calls) == 2, "Double-passe doit effectuer exactement 2 appels LLM"


class TestLLMDossierExtractorMultiSection:
    """Vérifie que l'extracteur peut remplir plusieurs sections."""

    def test_incendie_multi_section(self):
        mock = MockLLMProvider({
            "intervenants": {
                "nom_assure": "Sophie Bernard",
                "qualite_assure": "Propriétaire",
            },
            "contrat": {
                "type": "Particulier",
                "description_risque": "Maison individuelle de 120 m²",
            },
            "sinistre": {
                "date": "2025-11-28",
                "type": "Incendie",
                "localisation": "Cuisine",
                "circonstances": "Départ de feu sur plaque de cuisson",
                "causes": "Surchauffe huile de friture",
            },
            "dommages": {
                "items": [
                    {"designation": "Réfrigérateur", "categorie": "mobilier", "pu_ht": 650},
                ],
            },
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier(INCENDIE_MULTI_SECTION))
        assert result.intervenants.nom_assure == "Sophie Bernard"
        assert result.contrat.type == "Particulier"
        assert result.sinistre.type == "Incendie"
        assert len(result.dommages.items) == 1
        assert result.dommages.items[0].pu_ht == 650

    def test_vol_extraction(self):
        mock = MockLLMProvider({
            "intervenants": {"nom_assure": "Jean-Pierre Moreau", "qualite_assure": "Locataire"},
            "sinistre": {
                "date": "2026-01-05",
                "type": "Vol",
                "circonstances": "Cambriolage constaté au retour de vacances, porte fracturée",
            },
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier(VOL_AVEC_INTERRUPTIONS))
        assert result.sinistre.type == "Vol"
        assert result.intervenants.nom_assure == "Jean-Pierre Moreau"


class TestLLMDossierExtractorContext:
    """Vérifie le passage de contexte (champs existants)."""

    def test_existing_data_in_user_message(self):
        mock = MockLLMProvider({})
        extractor = LLMDossierExtractor(mock)
        asyncio.run(
            extractor.extract_dossier(
                "test",
                context={
                    "existing_data": {"sinistre": {"type": "Incendie"}},
                },
            )
        )
        # CHAMPS_DEJA_REMPLIS doit apparaître dans la Passe A (sinistre fait partie du group A)
        assert "CHAMPS_DEJA_REMPLIS" in mock.calls[0]["user_message"]
        assert "Incendie" in mock.calls[0]["user_message"]

    def test_no_context_no_extras(self):
        mock = MockLLMProvider({})
        extractor = LLMDossierExtractor(mock)
        asyncio.run(extractor.extract_dossier("test"))
        assert all("CHAMPS_DEJA_REMPLIS" not in c["user_message"] for c in mock.calls)

    def test_existing_data_routed_to_correct_pass(self):
        """Données existantes de conclusion envoyées uniquement à la Passe B."""
        mock = MockLLMProvider({})
        extractor = LLMDossierExtractor(mock)
        asyncio.run(
            extractor.extract_dossier(
                "test",
                context={
                    "existing_data": {
                        "conclusion": {"convention": "IRSI T2"},
                        "sinistre": {"type": "Vol"},
                    },
                },
            )
        )
        # Passe A (index 0) : reçoit sinistre, pas conclusion
        assert "Vol" in mock.calls[0]["user_message"]
        assert "IRSI T2" not in mock.calls[0]["user_message"]
        # Passe B (index 1) : reçoit conclusion, pas sinistre
        assert "IRSI T2" in mock.calls[1]["user_message"]


class TestLLMDossierExtractorFallback:
    """Vérifie le fallback vers le regex si le LLM échoue."""

    def test_fallback_on_llm_error(self):
        class FailingProvider(LLMProviderInterface):
            async def complete_json(self, system_prompt, user_message):
                raise ConnectionError("Ollama indisponible")

        from src.providers.nlp_extractor import FrenchInsuranceExtractor

        extractor = LLMDossierExtractor(
            FailingProvider(),
            fallback=FrenchInsuranceExtractor(),
        )
        result = asyncio.run(extractor.extract_dossier(SIMPLE_DEGAT_EAUX))
        # Le fallback regex doit quand même extraire le type sinistre
        assert result.sinistre is not None
        assert result.sinistre.type is not None


class TestNewFieldsCoverage:
    """Vérifie que TOUS les nouveaux champs sont supportés par les modèles."""

    def test_convoque_present_assure(self):
        mock = MockLLMProvider({
            "intervenants": {
                "nom_assure": "Martin Dupont",
                "convoque_assure": True,
                "present_assure": True,
            },
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("test"))
        assert result.intervenants.convoque_assure is True
        assert result.intervenants.present_assure is True

    def test_tiers_convoque_present(self):
        mock = MockLLMProvider({
            "intervenants": {
                "tiers": [
                    {"nom": "AXA", "role": "Compagnie d'assurance", "convoque": True, "present": False},
                    {"nom": "Cabinet Expert", "role": "Expert", "convoque": True, "present": True},
                ],
            },
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("test"))
        assert len(result.intervenants.tiers) == 2
        assert result.intervenants.tiers[0].convoque is True
        assert result.intervenants.tiers[0].present is False
        assert result.intervenants.tiers[1].present is True

    def test_dommage_vetuste(self):
        mock = MockLLMProvider({
            "dommages": {
                "items": [
                    {"designation": "Réfrigérateur", "categorie": "mobilier", "pu_ht": 650, "vet": 40},
                    {"designation": "Peinture plafond", "categorie": "embellissement", "pu_ht": 200, "vet": 0},
                ],
            },
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("test"))
        assert result.dommages.items[0].vet == 40
        assert result.dommages.items[1].vet == 0

    def test_franchise(self):
        mock = MockLLMProvider({
            "indemnisation": {"franchise": 150.0},
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("franchise de 150 euros"))
        assert result.indemnisation.franchise == 150.0

    def test_recours(self):
        mock = MockLLMProvider({
            "conclusion": {
                "recours": [
                    "Recours amiable famille Nguyen",
                    "Mise en demeure syndic",
                ],
            },
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("test"))
        assert len(result.conclusion.recours) == 2
        assert "Nguyen" in result.conclusion.recours[0]

    def test_notes(self):
        mock = MockLLMProvider({
            "notes": "Relancer le client avant vendredi",
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("test"))
        assert result.notes == "Relancer le client avant vendredi"

    def test_statut(self):
        mock = MockLLMProvider({
            "statut": "En cours",
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("test"))
        assert result.statut == "En cours"

    def test_full_dossier_all_fields(self):
        """Test exhaustif — TOUS les champs possibles remplis."""
        mock = MockLLMProvider({
            "intervenants": {
                "nom_assure": "SAS Boulangerie Lecomte",
                "qualite_assure": "Gérant",
                "convoque_assure": True,
                "present_assure": True,
                "date_rdv": "2026-02-10",
                "heure_debut": "08:30",
                "heure_fin": "10:30",
                "tiers": [
                    {"nom": "Groupama Pro", "role": "Compagnie d'assurance", "convoque": True, "present": True},
                    {"nom": "Cabinet Bertrand", "role": "Expert contradicteur", "convoque": True, "present": False},
                ],
            },
            "contrat": {
                "type": "Professionnel",
                "description_risque": "Local commercial boulangerie 180 m²",
                "conformite": "Oui",
                "conformite_description": "Contrat pro multirisque, garanties PE incluses",
            },
            "sinistre": {
                "date": "2026-02-05",
                "type": "Dégât des eaux",
                "localisation": "Laboratoire (arrière-boutique)",
                "tiers_implique": True,
                "circonstances": "Rupture de canalisation mur mitoyen",
                "causes": "Canalisation vétuste, responsabilité syndic",
                "dommages_desc": "Four pro endommagé, sol fissuré, murs humides",
            },
            "dommages": {
                "items": [
                    {"designation": "Reprise carrelage", "categorie": "immobilier", "qte": 15, "unite": "m²", "pu_ht": 85, "vet": 5},
                    {"designation": "Four Bongard", "categorie": "mobilier", "qte": 1, "unite": "U", "pu_ht": 12000, "vet": 20},
                    {"designation": "Pertes exploitation", "categorie": "autres", "qte": 3, "unite": "U", "pu_ht": 1200, "vet": 0},
                ],
            },
            "indemnisation": {"franchise": 500},
            "conclusion": {
                "responsabilites": "Responsabilité syndic engagée",
                "convention": "IRSI T2",
                "garantie_acquise": "Oui",
                "avec_reserve": True,
                "garantie_applicable": "Dégât des eaux",
                "beneficiaire": "SAS Boulangerie Lecomte",
                "garantie_description": "Garantie DDE pro + PE applicable",
                "conclusion_expert": "Sinistre pris en charge sous réserve",
                "recours": ["Mise en demeure syndic RAR 2026-02-12"],
            },
            "notes": "Sinistre important. Expert spécialisé commercial requis.",
            "statut": "En cours",
        })
        extractor = LLMDossierExtractor(mock)
        result = asyncio.run(extractor.extract_dossier("test"))

        # Intervenants
        assert result.intervenants.nom_assure == "SAS Boulangerie Lecomte"
        assert result.intervenants.qualite_assure == "Gérant"
        assert result.intervenants.convoque_assure is True
        assert result.intervenants.present_assure is True
        assert result.intervenants.date_rdv == "2026-02-10"
        assert result.intervenants.heure_debut == "08:30"
        assert result.intervenants.heure_fin == "10:30"
        assert len(result.intervenants.tiers) == 2
        assert result.intervenants.tiers[0].convoque is True
        assert result.intervenants.tiers[1].present is False

        # Contrat
        assert result.contrat.type == "Professionnel"
        assert result.contrat.conformite == "Oui"
        assert "180 m²" in result.contrat.description_risque

        # Sinistre
        assert result.sinistre.date == "2026-02-05"
        assert result.sinistre.type == "Dégât des eaux"
        assert result.sinistre.tiers_implique is True
        assert result.sinistre.circonstances is not None
        assert result.sinistre.causes is not None

        # Dommages
        assert len(result.dommages.items) == 3
        assert result.dommages.items[0].vet == 5
        assert result.dommages.items[1].pu_ht == 12000
        assert result.dommages.items[2].categorie == "autres"

        # Indemnisation
        assert result.indemnisation.franchise == 500

        # Conclusion
        assert result.conclusion.convention == "IRSI T2"
        assert result.conclusion.garantie_acquise == "Oui"
        assert result.conclusion.avec_reserve is True
        assert len(result.conclusion.recours) == 1
        assert result.conclusion.beneficiaire == "SAS Boulangerie Lecomte"

        # Notes & Statut
        assert "Expert spécialisé" in result.notes
        assert result.statut == "En cours"
