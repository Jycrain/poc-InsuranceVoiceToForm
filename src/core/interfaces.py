"""
Core abstractions — SOLID / DIP.
Aucune implémentation concrète ici, uniquement des contrats.
"""
from abc import ABC, abstractmethod
from pathlib import Path

from src.core.models import FormulaireExpertise


class STTInterface(ABC):
    """
    Contrat pour tout moteur Speech-to-Text.
    O/C : on peut ajouter Whisper, Wav2Vec, etc. sans toucher la logique métier.
    L   : toutes les implémentations sont substituables.
    """

    @abstractmethod
    def transcribe_file(self, audio_path: Path) -> str:
        """Transcrire un fichier audio et retourner le texte brut."""

    @abstractmethod
    def transcribe_stream(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """Transcrire un flux audio brut (PCM 16-bit)."""


class NLPParserInterface(ABC):
    """
    Contrat pour tout extracteur de champs depuis du texte.
    I   : le parser ne dépend pas du moteur STT.
    """

    @abstractmethod
    def extract(self, transcription: str) -> FormulaireExpertise:
        """
        Extraire les champs du formulaire sinistre depuis une transcription.
        """
