"""
Tests d'intégration — API FastAPI (sans moteur STT).
On teste uniquement l'endpoint /extract-text pour éviter la dépendance NeMo.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_extract_text_degat_eaux():
    r = client.post(
        "/api/v1/extract-text",
        data={"text": "Le 24 février, j'ai eu une fuite d'eau dans ma cuisine."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["type_sinistre"] == "Dégât des eaux"
    assert body["localisation"] == "Cuisine"


def test_extract_text_incendie():
    r = client.post(
        "/api/v1/extract-text",
        data={"text": "Un incendie s'est déclaré dans le garage."},
    )
    assert r.status_code == 200
    assert r.json()["type_sinistre"] == "Incendie"


def test_extract_text_transcription_brute():
    texte = "Vol constaté le 01/01/2026 dans ma chambre."
    r = client.post("/api/v1/extract-text", data={"text": texte})
    assert r.status_code == 200
    assert r.json()["transcription_brute"] == texte


def test_extract_text_champs_manquants():
    r = client.post("/api/v1/extract-text", data={"text": "Bonjour, j'appelle pour un sinistre."})
    assert r.status_code == 200
    body = r.json()
    assert body["date_sinistre"] is None
    assert body["type_sinistre"] is None


# ---------------------------------------------------------------------------
# Tests de l'endpoint /extract-dossier (LLM)
# ---------------------------------------------------------------------------


def test_extract_dossier_endpoint_exists():
    """L'endpoint /extract-dossier doit répondre (même si Ollama est absent)."""
    r = client.post(
        "/api/v1/extract-dossier",
        data={
            "text": "Le 24 février j'ai eu une fuite d'eau dans ma cuisine.",
            "current_section": "sinistre",
            "existing_data": "{}",
        },
    )
    # 200 si Ollama tourne ou si le fallback regex prend le relais
    # 500 uniquement si un bug interne (pas attendu)
    assert r.status_code == 200
    body = r.json()
    # Le fallback regex doit au minimum renvoyer la section sinistre
    assert "sinistre" in body or body == {}


def test_extract_dossier_with_existing_data():
    """L'endpoint accepte existing_data sans erreur."""
    r = client.post(
        "/api/v1/extract-dossier",
        data={
            "text": "Il y a eu un incendie dans le garage.",
            "current_section": "sinistre",
            "existing_data": '{"sinistre": {"type": "Incendie"}}',
        },
    )
    assert r.status_code == 200
