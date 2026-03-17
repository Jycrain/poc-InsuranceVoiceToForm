"""
Extracteur LLM — mapping transcription → DossierExtraction via IA.

Architecture double-passe séquentielle :
  Passe A : Personnes + Faits  (intervenants, contrat, sinistre)
  Passe B : Financier + Légal  (dommages, indemnisation, conclusion)

Chaque passe a un prompt court et un schéma en prose (sans placeholders),
ce qui évite que Mistral 7B retourne les valeurs template littéralement.

Fallback automatique vers FrenchInsuranceExtractor si le LLM est indisponible.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from src.core.interfaces import LLMProviderInterface, NLPParserInterface
from src.core.models import (
    DossierExtraction,
    FormulaireExpertise,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Passe A — Personnes & Faits : intervenants, contrat, sinistre
# ---------------------------------------------------------------------------

_SYSTEM_A = """\
Tu es un assistant expert sinistre. Extrais les informations de la transcription.
Règles strictes :
- N'inclus QUE les champs dont la valeur est EXPLICITEMENT dans la transcription. Omets tout le reste.
- Dates au format YYYY-MM-DD uniquement (jamais d'heure dans une date).
- Date du RDV d'expertise → intervenants.date_rdv. Date de l'événement sinistre → sinistre.date. Ces deux dates sont toujours différentes.
- Toute personne autre que l'assuré principal (conjoint, voisin, artisan…) → intervenants.tiers[].
- convoque_assure, present_assure, tiers[].convoque, tiers[].present : inclure SEULEMENT si "convoqué" ou "présent" est explicitement dit pour cette personne dans la transcription.
- sinistre.localisation = adresse ou pièce où le sinistre s'est produit. Jamais un nom de bien endommagé.
- Réponds UNIQUEMENT avec du JSON valide.\
"""

_SCHEMA_A = """\

Retourne un JSON contenant uniquement les champs trouvés dans la transcription, parmi :
{
  "intervenants": {
    "nom_assure": "Nom complet de l assuré",
    "qualite_assure": "Propriétaire" ou "Locataire" ou "Copropriétaire" ou "Gérant",
    "convoque_assure": true ou false (seulement si explicitement mentionné),
    "present_assure": true ou false (seulement si explicitement mentionné),
    "date_rdv": "date du rendez-vous au format YYYY-MM-DD",
    "heure_debut": "heure de début au format HH:MM",
    "heure_fin": "heure de fin au format HH:MM",
    "tiers": [{"nom": "Nom complet", "role": "Rôle (conjoint, voisin…)", "convoque": true/false, "present": true/false}]
  },
  "contrat": {
    "type": "Particulier" ou "Professionnel",
    "description_risque": "Description du risque assuré",
    "conformite": "Oui" ou "Non" ou "Non vérifié",
    "conformite_description": "Description de la conformité"
  },
  "sinistre": {
    "date": "date de l événement au format YYYY-MM-DD",
    "type": "Dégât des eaux" ou "Incendie" ou "Vol" ou "Bris de glace" ou "Autre",
    "localisation": "adresse ou pièce (jamais un bien endommagé)",
    "tiers_implique": true ou false,
    "circonstances": "Description des circonstances",
    "causes": "Description des causes",
    "dommages_desc": "Description générale des dommages"
  }
}\
"""

# ---------------------------------------------------------------------------
# Passe B — Financier & Conclusion : dommages, indemnisation, conclusion
# ---------------------------------------------------------------------------

_SYSTEM_B = """\
Tu es un assistant expert sinistre. Extrais les informations de la transcription.
Règles strictes :
- N'inclus QUE les champs dont la valeur est EXPLICITEMENT dans la transcription. Omets tout le reste.
- Tout bien endommagé ou volé avec un montant cité (même approximatif "environ X€") → dommages.items[]. Un item par bien. Si montant global pour un ensemble → unite="forfait".
- Convention — normalise les variantes phonétiques : "ircité 2"/"irsi 2" → "IRSI T2" ; "ircité 1"/"irsi 1" → "IRSI T1" ; "cite cop"/"cide cop" → "CIDE-COP" ; "sipiec"/"cipiec" → "CIPIEC".
- "avec réserve" ou "sous réserve" → avec_reserve=true ET garantie_acquise="Oui".
- garantie_applicable : type de sinistre couvert, avec majuscule initiale (ex: "Vol", "Dégât des eaux").
- notes : inclure SEULEMENT si la transcription contient explicitement "en note", "dans les notes", "on peut noter", "ajouter dans les notes". Sinon, ne PAS inclure ce champ.
- Réponds UNIQUEMENT avec du JSON valide.\
"""

_SCHEMA_B = """\

Retourne un JSON contenant uniquement les champs trouvés dans la transcription, parmi :
{
  "dommages": {
    "items": [
      {"designation": "Nom du bien", "categorie": "mobilier" ou "immobilier" ou "embellissement" ou "autres", "qte": nombre, "unite": "U" ou "m²" ou "forfait", "pu_ht": montant numérique, "vet": pourcentage vétusté 0-100}
    ]
  },
  "indemnisation": {
    "franchise": montant numérique en euros
  },
  "conclusion": {
    "responsabilites": "Description des responsabilités",
    "convention": "IRSI T1" ou "IRSI T2" ou "CIDE-COP" ou "CIPIEC" ou "Cumul Ass." ou "Sans objet" ou "Autre",
    "garantie_acquise": "Oui" ou "Non",
    "avec_reserve": true ou false,
    "garantie_applicable": "Type de garantie applicable (ex: Vol, Dégât des eaux)",
    "beneficiaire": "Nom du bénéficiaire",
    "garantie_description": "Description de la garantie",
    "conclusion_expert": "Conclusion de l expert"
  },
  "notes": "SEULEMENT si explicitement dicté par l utilisateur"
}\
"""


# ---------------------------------------------------------------------------
# Classe principale
# ---------------------------------------------------------------------------


class LLMDossierExtractor(NLPParserInterface):
    """
    Extracteur double-passe séquentielle via LLM.

    Passe A (personnes/faits) puis Passe B (financier/conclusion).
    Chaque appel gère ~15 champs → fiabilité bien supérieure à un
    seul appel de 30+ champs avec Mistral 7B.
    """

    def __init__(
        self,
        llm_provider: LLMProviderInterface,
        fallback: NLPParserInterface | None = None,
    ) -> None:
        self._llm = llm_provider
        self._fallback = fallback

    def extract(self, transcription: str) -> FormulaireExpertise:
        """Legacy : extraction sinistre uniquement (backward compat)."""
        if self._fallback:
            return self._fallback.extract(transcription)
        return FormulaireExpertise(transcription_brute=transcription)

    async def extract_dossier(
        self,
        transcription: str,
        context: Optional[dict[str, Any]] = None,
    ) -> DossierExtraction:
        msg_a = _build_message(transcription, context, _SCHEMA_A,
                               sections=("intervenants", "contrat", "sinistre"))
        msg_b = _build_message(transcription, context, _SCHEMA_B,
                               sections=("dommages", "indemnisation", "conclusion"))

        try:
            # Ollama traite sur GPU unique → appels séquentiels
            raw_a = await self._llm.complete_json(_SYSTEM_A, msg_a)
            raw_b = await self._llm.complete_json(_SYSTEM_B, msg_b)
            merged = _merge(_clean_llm_response(raw_a), _clean_llm_response(raw_b))
            return DossierExtraction(**merged)

        except Exception as exc:
            logger.warning("LLM extraction échouée, fallback regex : %s", exc)
            if self._fallback:
                return await self._fallback.extract_dossier(transcription, context)
            return DossierExtraction(notes=transcription[:200])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_message(
    transcription: str,
    context: Optional[dict[str, Any]],
    schema_hint: str,
    sections: tuple[str, ...],
) -> str:
    parts = [f"TRANSCRIPTION :\n{transcription}"]

    if context:
        existing = context.get("existing_data")
        if existing:
            relevant = {k: v for k, v in existing.items() if k in sections and v}
            if relevant:
                parts.append(
                    f"\nCHAMPS_DEJA_REMPLIS (conserver, compléter les manquants) :\n"
                    f"{json.dumps(relevant, ensure_ascii=False)}"
                )

    parts.append(schema_hint)
    return "\n".join(parts)


def _merge(a: dict, b: dict) -> dict:
    """Fusionne les résultats des deux passes. A est prioritaire sur B."""
    result = dict(a)
    for key, val in b.items():
        if key not in result:
            result[key] = val
        elif isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = {**val, **result[key]}
    return result


# ---------------------------------------------------------------------------
# Nettoyage des réponses LLM
# ---------------------------------------------------------------------------

_JUNK_VALUES = {
    "", "null", "non spécifié", "non fourni", "non mentionné",
    "non précisé", "non renseigné", "à déterminer", "inconnu",
    "n/a", "na", "none", "aucun", "aucune", "néant",
    "not specified", "not mentioned", "unknown",
    "description du bien assuré", "description...", "...",
}


def _is_junk(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _JUNK_VALUES or not value.strip()
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def _clean_dict(d: dict) -> dict | None:
    cleaned = {}
    for key, value in d.items():
        if isinstance(value, dict):
            sub = _clean_dict(value)
            if sub:
                cleaned[key] = sub
        elif isinstance(value, list):
            if len(value) > 0:
                clean_list = []
                for item in value:
                    if isinstance(item, dict):
                        sub = _clean_dict(item)
                        if sub:
                            clean_list.append(sub)
                    elif not _is_junk(item):
                        clean_list.append(item)
                if clean_list:
                    cleaned[key] = clean_list
        elif not _is_junk(value):
            cleaned[key] = value
    return cleaned if cleaned else None


def _clean_llm_response(raw: dict) -> dict:
    result = _clean_dict(raw)
    if not result:
        return {}

    # Normaliser les dates ISO datetime → date seule (ex: "2026-01-08T17:00" → "2026-01-08")
    iv = result.get("intervenants", {})
    for field in ("date_rdv",):
        if field in iv and isinstance(iv[field], str) and "T" in iv[field]:
            iv[field] = iv[field].split("T")[0]

    si = result.get("sinistre", {})
    if "date" in si and isinstance(si["date"], str) and "T" in si["date"]:
        si["date"] = si["date"].split("T")[0]

    # Normaliser la casse de garantie_applicable
    co = result.get("conclusion", {})
    if "garantie_applicable" in co and isinstance(co["garantie_applicable"], str):
        co["garantie_applicable"] = co["garantie_applicable"].capitalize()

    # Supprimer les items dommages sans prix réel + normaliser la casse catégorie
    if "dommages" in result and "items" in result["dommages"]:
        valid_items = []
        for item in result["dommages"]["items"]:
            try:
                price = float(item.get("pu_ht", 0) or 0)
            except (ValueError, TypeError):
                price = 0
            if price > 0:
                # Normaliser la catégorie en minuscules (frontend attend "mobilier" pas "Mobilier")
                if "categorie" in item and isinstance(item["categorie"], str):
                    item["categorie"] = item["categorie"].lower()
                valid_items.append(item)
        result["dommages"]["items"] = valid_items
        if not valid_items:
            del result["dommages"]

    return result
