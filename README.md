# Insurance Voice-to-Form (IVF)

Pipeline **Speech-to-Text → NLP** pour pré-remplir automatiquement un formulaire d'expertise sinistre à partir de la voix d'un assuré.

## Architecture

```
Audio (WAV/FLAC/MP3)
        │
        ▼
 STTInterface          ← abstraction (SOLID O/C, L)
        │
 ParakeetTranscriber   ← NVIDIA NeMo Parakeet
        │  transcription (str)
        ▼
 NLPParserInterface    ← abstraction
        │
 FrenchInsuranceExtractor  ← règles regex + keywords FR
        │
        ▼
 FormulaireExpertise   ← Pydantic
        │
        ▼
 FastAPI  /api/v1/upload-audio → JSON
```

## Installation rapide (sans GPU / sans NeMo)

```bash
pip install -e ".[dev]"
```

## Lancement de l'API

```bash
uvicorn src.api.app:app --reload
```

Swagger UI disponible sur : http://localhost:8000/docs

## Tests

```bash
pytest
```

## Endpoints

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/api/v1/health` | Healthcheck |
| POST | `/api/v1/upload-audio` | Audio → FormulaireExpertise |
| POST | `/api/v1/transcribe` | Audio → texte brut |
| POST | `/api/v1/extract-text` | Texte → FormulaireExpertise |

## Exemple

**Input :**
```
"Le 24 février, j'ai eu une fuite d'eau dans ma cuisine à cause du lave-vaisselle."
```

**Output :**
```json
{
  "date_sinistre": "2026-02-24",
  "type_sinistre": "Dégât des eaux",
  "localisation": "Cuisine",
  "tiers_implique": false,
  "description_courte": "Dégât des eaux — Cuisine (\"Le 24 février, j'ai eu une fuite d'eau dans ma cuisine à cause du lave-vaisselle.\")"
}
```

## Extension du moteur STT

Pour passer de Parakeet à Whisper, créer `src/providers/stt_whisper.py` :

```python
from src.core.interfaces import STTInterface

class WhisperTranscriber(STTInterface):
    def transcribe_file(self, audio_path): ...
    def transcribe_stream(self, audio_bytes, sample_rate): ...
```

Aucune modification de la logique métier ni de l'API.
