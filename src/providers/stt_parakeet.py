"""
Implémentation STT — NVIDIA NeMo Parakeet.

Parakeet (parakeet-tdt-0.6b-v2) est optimisé pour l'anglais.
Pour le français, on peut substituer un modèle NeMo francophone
(ex: stt_fr_conformer_ctc_large) sans changer l'interface.

O/C & L : ParakeetTranscriber est substituable par n'importe quelle
autre classe implémentant STTInterface.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.core.interfaces import STTInterface
from src.utils.audio import bytes_to_wav, load_and_resample

logger = logging.getLogger(__name__)


class ParakeetTranscriber(STTInterface):
    """
    Moteur STT NeMo Parakeet.

    Args:
        model_name: Identifiant NeMo du modèle à charger.
        device: "cuda" ou "cpu".
    """

    DEFAULT_MODEL = "nvidia/parakeet-tdt-0.6b-v2"
    FRENCH_MODEL = "nvidia/stt_fr_conformer_ctc_large"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
    ) -> None:
        self.model_name = model_name
        self.device = device
        self._model: Optional[object] = None

    def _load_model(self) -> None:
        """Chargement paresseux (lazy) du modèle NeMo."""
        if self._model is not None:
            return
        try:
            import nemo.collections.asr as nemo_asr  # type: ignore

            logger.info("Chargement du modèle NeMo : %s", self.model_name)
            self._model = nemo_asr.models.ASRModel.from_pretrained(
                model_name=self.model_name,
                map_location=self.device,
            )
            self._model.eval()
            logger.info("Modèle chargé avec succès.")
        except ImportError as exc:
            raise RuntimeError(
                "NeMo toolkit introuvable. Installez-le : "
                "pip install nemo_toolkit['asr']"
            ) from exc

    def transcribe_file(self, audio_path: Path) -> str:
        self._load_model()
        # NeMo attend un fichier WAV 16 kHz mono
        waveform, sr = load_and_resample(audio_path)

        import tempfile
        import soundfile as sf  # type: ignore

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, waveform, sr)
            tmp_path = tmp.name

        results = self._model.transcribe([tmp_path])  # type: ignore[union-attr]
        transcription: str = results[0] if isinstance(results[0], str) else results[0].text
        logger.debug("Transcription : %s", transcription)
        return transcription

    def transcribe_stream(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        self._load_model()
        tmp_path = bytes_to_wav(audio_bytes, sample_rate)
        try:
            results = self._model.transcribe([str(tmp_path)])  # type: ignore[union-attr]
            transcription: str = (
                results[0] if isinstance(results[0], str) else results[0].text
            )
        finally:
            tmp_path.unlink(missing_ok=True)
        return transcription
