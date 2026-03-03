"""
API FastAPI — endpoints du projet IVF.

Endpoints :
  POST /upload-audio  → transcription + extraction → FormulaireExpertise (JSON)
  POST /transcribe    → transcription brute uniquement
  POST /extract-text  → extraction à partir d'un texte déjà transcrit
  GET  /health        → healthcheck
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.core.models import FormulaireExpertise
from src.providers.nlp_extractor import FrenchInsuranceExtractor
from src.providers.stt_parakeet import ParakeetTranscriber

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


async def _read_upload(file: UploadFile) -> bytes:
    """Lit le contenu d'un fichier uploadé avec vérification de taille."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux. Maximum : {MAX_UPLOAD_BYTES // 1024 // 1024} MB.",
        )
    return content


def _safe_unlink(path: Path | None) -> None:
    """Supprime un fichier temporaire sans lever d'exception."""
    if path is not None:
        path.unlink(missing_ok=True)

# ---------------------------------------------------------------------------
# Dépendances (instanciation unique — lazy loading du modèle NeMo)
# ---------------------------------------------------------------------------
_transcriber: ParakeetTranscriber | None = None
_extractor = FrenchInsuranceExtractor()


def _get_transcriber(model_name: str | None = None) -> ParakeetTranscriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = ParakeetTranscriber(
            model_name=model_name or ParakeetTranscriber.DEFAULT_MODEL
        )
    return _transcriber


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health", summary="Vérification de l'état du service")
async def health() -> dict:
    return {"status": "ok", "service": "IVF — Insurance Voice-to-Form"}


@router.post(
    "/upload-audio",
    response_model=FormulaireExpertise,
    summary="Transcrire un fichier audio et extraire le formulaire sinistre",
    status_code=status.HTTP_200_OK,
)
async def upload_audio(
    file: UploadFile = File(..., description="Fichier audio (WAV, FLAC, MP3…)"),
    model: str = Form(
        default=ParakeetTranscriber.DEFAULT_MODEL,
        description="Identifiant NeMo du modèle STT à utiliser.",
    ),
) -> FormulaireExpertise:
    """
    Pipeline complet : Audio → STT → NLP → FormulaireExpertise.
    """
    content = await _read_upload(file)
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        transcriber = _get_transcriber(model)
        transcription = transcriber.transcribe_file(tmp_path)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erreur STT")
        raise HTTPException(status_code=500, detail=f"Erreur STT : {exc}") from exc
    finally:
        _safe_unlink(tmp_path)

    return _extractor.extract(transcription)


@router.post(
    "/transcribe",
    summary="Transcription brute uniquement (sans extraction de champs)",
    status_code=status.HTTP_200_OK,
)
async def transcribe_only(
    file: UploadFile = File(...),
    model: str = Form(default=ParakeetTranscriber.DEFAULT_MODEL),
) -> dict:
    content = await _read_upload(file)
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        transcription = _get_transcriber(model).transcribe_file(tmp_path)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        _safe_unlink(tmp_path)

    return {"transcription": transcription}


@router.post(
    "/extract-text",
    response_model=FormulaireExpertise,
    summary="Extraction de champs depuis un texte déjà transcrit",
    status_code=status.HTTP_200_OK,
)
async def extract_from_text(text: str = Form(..., description="Texte transcrit")) -> FormulaireExpertise:
    """
    Utile pour tester l'extracteur sans passer par le moteur STT.
    """
    return _extractor.extract(text)
