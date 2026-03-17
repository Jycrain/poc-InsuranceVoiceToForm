"""
Extracteur NLP — mapping transcription → FormulaireExpertise.

Stratégie V1 : regex + dictionnaire de mots-clés (aucune dépendance lourde).
Extension possible : remplacer par un LLM local (Mistral/Llama via Ollama)
sans modifier l'interface.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Optional

from typing import Any

from src.core.interfaces import NLPParserInterface
from src.core.models import (
    DossierExtraction,
    FormulaireExpertise,
    SinistreExtraction,
    TypeSinistre,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dictionnaires de mots-clés français
# ---------------------------------------------------------------------------

_TYPE_KEYWORDS: dict[TypeSinistre, list[str]] = {
    TypeSinistre.DEGAT_DES_EAUX: [
        "fuite", "fuite d'eau", "dégât des eaux", "inondation", "infiltration",
        "humidité", "tuyau", "plomberie", "robinet", "lave-vaisselle",
        "lave vaisselle", "machine à laver", "débordement", "condensation",
        "toiture", "gouttière",
    ],
    TypeSinistre.INCENDIE: [
        "incendie", "feu", "brûlure", "brûlé", "fumée", "flamme",
        "départ de feu", "carbonisé",
    ],
    TypeSinistre.VOL: [
        "vol", "cambriolage", "effraction", "subtilisé", "dérobé",
        "volé", "vandalisme",
    ],
    TypeSinistre.BRIS_DE_GLACE: [
        "bris de glace", "vitre cassée", "vitre brisée", "fenêtre brisée",
        "pare-brise", "glace brisée",
    ],
}

_PIECES: list[str] = [
    "cuisine", "salon", "salle de bain", "salle de séjour", "chambre",
    "toilettes", "wc", "bureau", "couloir", "cave", "grenier",
    "sous-sol", "balcon", "terrasse", "garage", "entrée", "hall",
    "véranda", "buanderie",
]

_TIERS_KEYWORDS: list[str] = [
    "voisin", "voisine", "locataire", "propriétaire", "tiers", "autre personne",
    "responsable", "responsabilité", "prestataire", "artisan", "plombier",
    "entreprise", "société",
]

# Patterns de date en français
_DATE_PATTERNS: list[tuple[str, str]] = [
    # "le 24 février 2026" / "le 24 février"
    (
        r"le\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|"
        r"septembre|octobre|novembre|décembre)(?:\s+(\d{4}))?",
        "dmy_fr",
    ),
    # "24/02/2026" ou "24-02-2026"
    (r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", "dmy_num"),
    # "2026-02-24"
    (r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})", "ymd_iso"),
]

_MONTHS_FR: dict[str, int] = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


# ---------------------------------------------------------------------------
# Helpers privés
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    return text.lower().strip()


def _extract_date(text: str) -> Optional[date]:
    norm = _normalise(text)
    current_year = datetime.now().year

    for pattern, fmt in _DATE_PATTERNS:
        m = re.search(pattern, norm)
        if not m:
            continue
        try:
            if fmt == "dmy_fr":
                day = int(m.group(1))
                month = _MONTHS_FR[m.group(2)]
                year = int(m.group(3)) if m.group(3) else current_year
                return date(year, month, day)
            if fmt == "dmy_num":
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if fmt == "ymd_iso":
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError as exc:
            logger.debug("Date invalide ignorée : %s", exc)

    return None


def _extract_type(text: str) -> Optional[TypeSinistre]:
    norm = _normalise(text)
    # On donne la priorité au type avec le plus de mots-clés trouvés
    scores: dict[TypeSinistre, int] = {}
    for stype, keywords in _TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in norm)
        if score:
            scores[stype] = score
    if not scores:
        return None
    return max(scores, key=lambda t: scores[t])


def _extract_localisation(text: str) -> Optional[str]:
    norm = _normalise(text)
    for piece in _PIECES:
        if piece in norm:
            return piece.capitalize()
    # Fallback : chercher un pattern "à/dans/en [lieu]"
    m = re.search(r"(?:dans|à|en)\s+([a-zéèêàùâîôûç\s]{3,30}?)(?:\s+(?:à|de|du|le|la|les|un|une|mon|ma)\b|[,\.]|$)", norm)
    if m:
        return m.group(1).strip().capitalize()
    return None


def _extract_tiers(text: str) -> bool:
    norm = _normalise(text)
    return any(kw in norm for kw in _TIERS_KEYWORDS)


def _build_description(text: str, type_sinistre: Optional[TypeSinistre], localisation: Optional[str]) -> str:
    parts: list[str] = []
    if type_sinistre:
        parts.append(type_sinistre.value if hasattr(type_sinistre, "value") else str(type_sinistre))
    if localisation:
        parts.append(f"— {localisation}")
    # Ajouter un extrait de la transcription (max 150 car.)
    snippet = text.strip()[:150]
    if snippet:
        parts.append(f'("{snippet}")')
    return " ".join(parts)[:200]


# ---------------------------------------------------------------------------
# Classe principale
# ---------------------------------------------------------------------------

class FrenchInsuranceExtractor(NLPParserInterface):
    """
    Extracteur de champs sinistre depuis du texte français.
    Basé sur des règles (regex + keywords) — sans modèle ML externe.

    Pour une précision supérieure, remplacer par LLMExtractor
    (même interface) qui appelle Mistral/Llama via API locale.
    """

    def extract(self, transcription: str) -> FormulaireExpertise:
        logger.debug("Extraction sur : %s", transcription[:100])

        date_sinistre = _extract_date(transcription)
        type_sinistre = _extract_type(transcription)
        localisation = _extract_localisation(transcription)
        tiers = _extract_tiers(transcription)
        description = _build_description(transcription, type_sinistre, localisation)

        return FormulaireExpertise(
            date_sinistre=date_sinistre,
            type_sinistre=type_sinistre,
            localisation=localisation,
            tiers_implique=tiers,
            description_courte=description or None,
            transcription_brute=transcription,
        )

    async def extract_dossier(
        self,
        transcription: str,
        context: dict[str, Any] | None = None,
    ) -> DossierExtraction:
        """Fallback regex : ne couvre que la section sinistre."""
        form = self.extract(transcription)
        return DossierExtraction(
            sinistre=SinistreExtraction(
                date=str(form.date_sinistre) if form.date_sinistre else None,
                type=form.type_sinistre,
                localisation=form.localisation,
                tiers_implique=form.tiers_implique,
                dommages_desc=form.description_courte,
            ),
        )
