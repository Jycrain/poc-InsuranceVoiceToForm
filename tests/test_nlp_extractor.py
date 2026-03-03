"""
Tests unitaires — FrenchInsuranceExtractor.
Couvre le cas d'exemple du .md et des variantes.
"""
import pytest
from datetime import date

from src.providers.nlp_extractor import FrenchInsuranceExtractor
from src.core.models import TypeSinistre

extractor = FrenchInsuranceExtractor()


class TestExempleSpec:
    """Cas d'exemple exact mentionné dans la spec."""

    def test_date(self):
        r = extractor.extract(
            "Le 24 février, j'ai eu une fuite d'eau dans ma cuisine à cause du lave-vaisselle."
        )
        assert r.date_sinistre == date(2026, 2, 24)

    def test_type(self):
        r = extractor.extract(
            "Le 24 février, j'ai eu une fuite d'eau dans ma cuisine à cause du lave-vaisselle."
        )
        assert r.type_sinistre == TypeSinistre.DEGAT_DES_EAUX.value

    def test_localisation(self):
        r = extractor.extract(
            "Le 24 février, j'ai eu une fuite d'eau dans ma cuisine à cause du lave-vaisselle."
        )
        assert r.localisation == "Cuisine"

    def test_tiers(self):
        r = extractor.extract(
            "Le 24 février, j'ai eu une fuite d'eau dans ma cuisine à cause du lave-vaisselle."
        )
        assert r.tiers_implique is False


class TestIncendie:
    def test_type_incendie(self):
        r = extractor.extract("Il y a eu un incendie dans le salon hier soir.")
        assert r.type_sinistre == TypeSinistre.INCENDIE.value

    def test_localisation_salon(self):
        r = extractor.extract("Il y a eu un incendie dans le salon hier soir.")
        assert r.localisation == "Salon"


class TestVol:
    def test_type_vol(self):
        r = extractor.extract("Mon appartement a subi un cambriolage le 10 mars.")
        assert r.type_sinistre == TypeSinistre.VOL.value

    def test_date_numerique(self):
        r = extractor.extract("Cambriolage le 10/03/2026.")
        assert r.date_sinistre == date(2026, 3, 10)


class TestTiers:
    def test_tiers_voisin(self):
        r = extractor.extract("C'est la fuite d'eau du voisin qui a causé des dégâts.")
        assert r.tiers_implique is True

    def test_tiers_plombier(self):
        r = extractor.extract("Le plombier a mal réparé le robinet.")
        assert r.tiers_implique is True


class TestDateFormats:
    def test_date_iso(self):
        r = extractor.extract("Sinistre survenu le 2026-02-24.")
        assert r.date_sinistre == date(2026, 2, 24)

    def test_date_slash(self):
        r = extractor.extract("Date du sinistre : 24/02/2026.")
        assert r.date_sinistre == date(2026, 2, 24)


class TestTranscriptionBrute:
    def test_transcription_conservee(self):
        texte = "Fuite d'eau dans la salle de bain."
        r = extractor.extract(texte)
        assert r.transcription_brute == texte
