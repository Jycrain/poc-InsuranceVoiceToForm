"""
Utilitaires audio : conversion, rééchantillonnage, validation.
NeMo Parakeet attend du PCM 16 kHz mono 16-bit.
"""
from __future__ import annotations

import io
import wave
from pathlib import Path

import numpy as np

try:
    import soundfile as sf
    _SF_AVAILABLE = True
except ImportError:
    _SF_AVAILABLE = False

try:
    import librosa
    _LIBROSA_AVAILABLE = True
except ImportError:
    _LIBROSA_AVAILABLE = False

TARGET_SAMPLE_RATE = 16_000
SUPPORTED_EXTENSIONS = {".wav", ".flac", ".ogg", ".mp3", ".m4a"}


class AudioProcessingError(Exception):
    pass


def validate_audio_file(path: Path) -> None:
    if not path.exists():
        raise AudioProcessingError(f"Fichier introuvable : {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise AudioProcessingError(
            f"Format non supporté '{path.suffix}'. Acceptés : {SUPPORTED_EXTENSIONS}"
        )


def load_and_resample(path: Path, target_sr: int = TARGET_SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """
    Charge un fichier audio et le rééchantillonne si nécessaire.
    Retourne (waveform_float32_mono, sample_rate).
    """
    validate_audio_file(path)

    if _LIBROSA_AVAILABLE:
        waveform, sr = librosa.load(str(path), sr=target_sr, mono=True)
        return waveform.astype(np.float32), sr

    if _SF_AVAILABLE:
        waveform, sr = sf.read(str(path), always_2d=False, dtype="float32")
        if waveform.ndim > 1:
            waveform = waveform.mean(axis=1)
        if sr != target_sr:
            raise AudioProcessingError(
                f"soundfile ne peut pas rééchantillonner ({sr} → {target_sr}). "
                "Installez librosa : pip install librosa"
            )
        return waveform, sr

    raise AudioProcessingError(
        "Aucune bibliothèque audio disponible. Installez : pip install librosa soundfile"
    )


def bytes_to_wav(audio_bytes: bytes, sample_rate: int = TARGET_SAMPLE_RATE) -> Path:
    """
    Écrit des octets PCM bruts dans un fichier .wav temporaire.
    Retourne le chemin du fichier créé.
    """
    import tempfile

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)
    return Path(tmp.name)


def waveform_to_wav_bytes(waveform: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE) -> bytes:
    """Convertit un tableau numpy float32 en bytes WAV (pour les tests)."""
    pcm = (waveform * 32767).astype(np.int16).tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()
