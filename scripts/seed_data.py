"""
Script de seed — crée des dossiers de test avec de fausses données réalistes.
Usage : python scripts/seed_data.py
"""
import json
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Ajouter la racine au path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.db.database import init_db, _connect

def _now():
    return datetime.now(timezone.utc).isoformat()

def insert(reference, statut, data, created_offset_days=0):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    created = (now - timedelta(days=created_offset_days)).isoformat()
    dossier_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO dossiers (id, reference, statut, created_at, updated_at, data) VALUES (?,?,?,?,?,?)",
            (dossier_id, reference, statut, created, now.isoformat(), json.dumps(data, ensure_ascii=False)),
        )
        conn.commit()
    print(f"  ✅ {reference} — {statut}")

# ── DOSSIER 1 : Dégât des eaux ────────────────────────────────────────────────
D1 = {
    "notes": "Client difficile à joindre. Relancer avant vendredi.",
    "rdv": [
        {
            "date": "2025-11-15",
            "heure_debut": "09:00",
            "heure_fin": "10:00",
            "assure": {"nom": "Martin Dupont", "qualite": "Propriétaire", "convoque": True, "present": True},
            "tiers": [
                {"nom": "AXA Assurances", "role": "Compagnie d'assurance", "convoque": True, "present": False},
                {"nom": "Cabinet Lefèvre", "role": "Expert", "convoque": True, "present": True},
            ],
        }
    ],
    "contrat": {
        "type": "Particulier",
        "description_risque": "Appartement de 85 m² au 3ème étage, immeuble années 70. Contrat MRH multirisque habitation.",
        "conformite": "Oui",
        "conformite_description": "Le risque décrit correspond aux garanties souscrites.",
    },
    "sinistre": {
        "date": "2025-11-10",
        "type": "Dégât des eaux",
        "localisation": "Salle de bains",
        "tiers_implique": False,
        "circonstances": "Fuite provenant du joint de la baignoire. Dommages constatés au plafond du salon du logement situé au dessous.",
        "causes": "Défaut d'étanchéité du joint silicone autour de la baignoire, vétusté avérée.",
        "dommages_desc": "Infiltration au plafond du voisin du dessous. Tache d'humidité de 2 m². Peinture décollée.",
        "transcription": "",
    },
    "dommages": {
        "categories": {
            "immobilier": [
                {"designation": "Reprise peinture plafond salon (2 m²)", "qte": 2, "unite": "m²", "pu_ht": 45, "vn": 90, "vet": 10},
                {"designation": "Remplacement joint baignoire", "qte": 1, "unite": "forfait", "pu_ht": 120, "vn": 120, "vet": 30},
            ],
            "embellissement": [],
            "mobilier": [
                {"designation": "Tableau abîmé par l'humidité", "qte": 1, "unite": "U", "pu_ht": 80, "vn": 80, "vet": 20},
            ],
            "autres": [],
        }
    },
    "indemnisation": {"franchise": 150},
    "conclusion": {
        "responsabilites": "Responsabilité de l'assuré engagée. Défaut d'entretien courant.",
        "recours": [],
        "convention": "IRSI T1",
        "garantie_acquise": "Oui",
        "avec_reserve": False,
        "garantie_applicable": "Dégât des eaux",
        "beneficiaire": "Martin Dupont",
        "garantie_description": "Garantie DDE applicable. Franchise contractuelle de 150 €.",
        "conclusion_expert": "Sinistre pris en charge. Montant total retenu : 290 € HT, franchise déduite : 140 €.",
    },
}

# ── DOSSIER 2 : Incendie (En cours) ──────────────────────────────────────────
D2 = {
    "notes": "RDV contradictoire prévu. Attente devis entreprise.",
    "rdv": [
        {
            "date": "2025-12-03",
            "heure_debut": "14:00",
            "heure_fin": "15:30",
            "assure": {"nom": "Sophie Bernard", "qualite": "Propriétaire", "convoque": True, "present": True},
            "tiers": [
                {"nom": "MAIF", "role": "Compagnie d'assurance", "convoque": True, "present": True},
            ],
        },
        {
            "date": "2025-12-17",
            "heure_debut": "10:00",
            "heure_fin": "11:00",
            "assure": {"nom": "Sophie Bernard", "qualite": "Propriétaire", "convoque": True, "present": False},
            "tiers": [],
        },
    ],
    "contrat": {
        "type": "Particulier",
        "description_risque": "Maison individuelle de 120 m², construction 1995. Contrat tous risques habitation.",
        "conformite": "Oui",
        "conformite_description": "",
    },
    "sinistre": {
        "date": "2025-11-28",
        "type": "Incendie",
        "localisation": "Cuisine",
        "tiers_implique": False,
        "circonstances": "Départ de feu sur la plaque de cuisson laissée sans surveillance. Intervention des pompiers à 22h15.",
        "causes": "Surchauffe de l'huile de friture. Origine accidentelle confirmée.",
        "dommages_desc": "Cuisine entièrement détruite. Dommages fumée dans séjour et couloir. Toiture légèrement touchée.",
        "transcription": "",
    },
    "dommages": {
        "categories": {
            "immobilier": [
                {"designation": "Reconstruction cuisine complète", "qte": 1, "unite": "forfait", "pu_ht": 8500, "vn": 8500, "vet": 15},
                {"designation": "Nettoyage dégâts fumée (séjour + couloir)", "qte": 35, "unite": "m²", "pu_ht": 28, "vn": 980, "vet": 0},
                {"designation": "Reprise toiture (tuiles)", "qte": 4, "unite": "m²", "pu_ht": 180, "vn": 720, "vet": 20},
            ],
            "embellissement": [
                {"designation": "Peinture séjour", "qte": 42, "unite": "m²", "pu_ht": 22, "vn": 924, "vet": 0},
            ],
            "mobilier": [
                {"designation": "Réfrigérateur", "qte": 1, "unite": "U", "pu_ht": 650, "vn": 650, "vet": 40},
                {"designation": "Micro-ondes", "qte": 1, "unite": "U", "pu_ht": 120, "vn": 120, "vet": 50},
                {"designation": "Vaisselle et ustensiles", "qte": 1, "unite": "forfait", "pu_ht": 300, "vn": 300, "vet": 30},
            ],
            "autres": [],
        }
    },
    "indemnisation": {"franchise": 300},
    "conclusion": {
        "responsabilites": "Sinistre accidentel. Aucune responsabilité tierce engagée.",
        "recours": [],
        "convention": "CIDE-COP",
        "garantie_acquise": "Oui",
        "avec_reserve": True,
        "garantie_applicable": "Incendie",
        "beneficiaire": "Sophie Bernard",
        "garantie_description": "Garantie incendie applicable. Réserve émise sur la vétusté du câblage électrique.",
        "conclusion_expert": "",
    },
}

# ── DOSSIER 3 : Vol (À traiter) ───────────────────────────────────────────────
D3 = {
    "notes": "",
    "rdv": [
        {
            "date": "2026-01-08",
            "heure_debut": "11:00",
            "heure_fin": "12:00",
            "assure": {"nom": "Jean-Pierre Moreau", "qualite": "Locataire", "convoque": True, "present": True},
            "tiers": [
                {"nom": "Allianz", "role": "Compagnie d'assurance", "convoque": False, "present": False},
            ],
        }
    ],
    "contrat": {
        "type": "Particulier",
        "description_risque": "Appartement T4, 95 m², 2ème étage sans ascenseur.",
        "conformite": "Non vérifié",
        "conformite_description": "",
    },
    "sinistre": {
        "date": "2026-01-05",
        "type": "Vol",
        "localisation": "Séjour / Chambre principale",
        "tiers_implique": False,
        "circonstances": "Cambriolage constaté au retour de vacances. Porte d'entrée fracturée. Plainte déposée au commissariat (récépissé joint).",
        "causes": "Effraction sur la serrure principale. Absence de système d'alarme.",
        "dommages_desc": "Ordinateur portable, bijoux, console de jeux et espèces dérobés.",
        "transcription": "",
    },
    "dommages": {
        "categories": {
            "immobilier": [
                {"designation": "Remplacement serrure 3 points", "qte": 1, "unite": "forfait", "pu_ht": 280, "vn": 280, "vet": 0},
                {"designation": "Réparation encadrement porte", "qte": 1, "unite": "forfait", "pu_ht": 150, "vn": 150, "vet": 0},
            ],
            "embellissement": [],
            "mobilier": [
                {"designation": "Ordinateur portable MacBook Pro 14\"", "qte": 1, "unite": "U", "pu_ht": 1800, "vn": 1800, "vet": 30},
                {"designation": "Console PlayStation 5", "qte": 1, "unite": "U", "pu_ht": 550, "vn": 550, "vet": 10},
                {"designation": "Bijoux (bague, collier, montre)", "qte": 1, "unite": "forfait", "pu_ht": 2200, "vn": 2200, "vet": 0},
            ],
            "autres": [
                {"designation": "Espèces", "qte": 1, "unite": "forfait", "pu_ht": 500, "vn": 500, "vet": 0},
            ],
        }
    },
    "indemnisation": {"franchise": 200},
    "conclusion": {
        "responsabilites": "",
        "recours": [],
        "convention": "",
        "garantie_acquise": "Non",
        "avec_reserve": False,
        "garantie_applicable": "Vol",
        "beneficiaire": "Jean-Pierre Moreau",
        "garantie_description": "",
        "conclusion_expert": "",
    },
}

# ── DOSSIER 4 : Bris de glace (Clôturé) ──────────────────────────────────────
D4 = {
    "notes": "Dossier clôturé. Indemnisation versée le 2025-10-22.",
    "rdv": [
        {
            "date": "2025-10-14",
            "heure_debut": "16:00",
            "heure_fin": "16:30",
            "assure": {"nom": "Camille Rousseau", "qualite": "Propriétaire", "convoque": True, "present": True},
            "tiers": [],
        }
    ],
    "contrat": {
        "type": "Particulier",
        "description_risque": "Appartement duplex, 65 m², fenêtres double vitrage.",
        "conformite": "Oui",
        "conformite_description": "Garantie bris de glace incluse au contrat.",
    },
    "sinistre": {
        "date": "2025-10-10",
        "type": "Bris de glace",
        "localisation": "Salon (baie vitrée)",
        "tiers_implique": True,
        "circonstances": "Ballon de football envoyé par un enfant du voisinage a brisé la baie vitrée principale du salon.",
        "causes": "Impact accidentel. Tiers identifié : famille Nguyen, appartement 4B.",
        "dommages_desc": "Baie vitrée 200x220 cm double vitrage entièrement brisée.",
        "transcription": "",
    },
    "dommages": {
        "categories": {
            "immobilier": [
                {"designation": "Remplacement baie vitrée double vitrage 200x220", "qte": 1, "unite": "U", "pu_ht": 1200, "vn": 1200, "vet": 0},
                {"designation": "Pose et dépose", "qte": 1, "unite": "forfait", "pu_ht": 250, "vn": 250, "vet": 0},
            ],
            "embellissement": [],
            "mobilier": [],
            "autres": [],
        }
    },
    "indemnisation": {"franchise": 100},
    "conclusion": {
        "responsabilites": "Responsabilité du tiers (famille Nguyen) retenue. Recours possible.",
        "recours": ["Recours amiable famille Nguyen — courrier envoyé le 2025-10-18"],
        "convention": "CIPIEC",
        "garantie_acquise": "Oui",
        "avec_reserve": False,
        "garantie_applicable": "Bris de glace",
        "beneficiaire": "Camille Rousseau",
        "garantie_description": "Garantie brise de glace applicable. Indemnisation immédiate, recours en cours.",
        "conclusion_expert": "Dossier simple. Remplacement effectué le 2025-10-20. Indemnité nette versée : 1 350 € (franchise 100 € déduite).",
    },
}

# ── DOSSIER 5 : Dégât des eaux professionnel (En cours) ──────────────────────
D5 = {
    "notes": "Sinistre important. Expert spécialisé commercial requis.",
    "rdv": [
        {
            "date": "2026-02-10",
            "heure_debut": "08:30",
            "heure_fin": "10:30",
            "assure": {"nom": "SAS Boulangerie Lecomte", "qualite": "Gérant", "convoque": True, "present": True},
            "tiers": [
                {"nom": "Groupama Pro", "role": "Compagnie d'assurance", "convoque": True, "present": True},
                {"nom": "Cabinet Bertrand & Fils", "role": "Expert contradicteur", "convoque": True, "present": False},
            ],
        }
    ],
    "contrat": {
        "type": "Professionnel",
        "description_risque": "Local commercial boulangerie 180 m², fonds de commerce, matériel professionnel.",
        "conformite": "Oui",
        "conformite_description": "Contrat pro multirisque. Garanties PE (pertes d'exploitation) incluses.",
    },
    "sinistre": {
        "date": "2026-02-05",
        "type": "Dégât des eaux",
        "localisation": "Laboratoire (arrière-boutique)",
        "tiers_implique": True,
        "circonstances": "Rupture de canalisation dans le mur mitoyen avec l'appartement du dessus. Inondation du laboratoire de boulangerie constatée à 5h du matin à l'ouverture.",
        "causes": "Canalisation d'alimentation vétuste, responsabilité du syndic de copropriété engagée.",
        "dommages_desc": "Four professionnel endommagé, sol carrelé fissuré, murs humides, pertes d'exploitation 3 jours.",
        "transcription": "",
    },
    "dommages": {
        "categories": {
            "immobilier": [
                {"designation": "Reprise carrelage laboratoire (15 m²)", "qte": 15, "unite": "m²", "pu_ht": 85, "vn": 1275, "vet": 5},
                {"designation": "Traitement humidité murs (injection)", "qte": 1, "unite": "forfait", "pu_ht": 1800, "vn": 1800, "vet": 0},
            ],
            "embellissement": [],
            "mobilier": [
                {"designation": "Four professionnel Bongard (remplacement)", "qte": 1, "unite": "U", "pu_ht": 12000, "vn": 12000, "vet": 20},
                {"designation": "Pétrin électrique endommagé", "qte": 1, "unite": "U", "pu_ht": 3500, "vn": 3500, "vet": 15},
            ],
            "autres": [
                {"designation": "Pertes d'exploitation (3 jours)", "qte": 3, "unite": "U", "pu_ht": 1200, "vn": 3600, "vet": 0},
                {"designation": "Denrées alimentaires perdues", "qte": 1, "unite": "forfait", "pu_ht": 800, "vn": 800, "vet": 0},
            ],
        }
    },
    "indemnisation": {"franchise": 500},
    "conclusion": {
        "responsabilites": "Responsabilité du syndic de copropriété (canalisation commune) engagée. Recours initié.",
        "recours": [
            "Mise en demeure syndic Immobilière du Centre — courrier RAR 2026-02-12",
            "Déclaration assurance responsabilité civile syndic en cours",
        ],
        "convention": "IRSI T2",
        "garantie_acquise": "Oui",
        "avec_reserve": True,
        "garantie_applicable": "Dégât des eaux",
        "beneficiaire": "SAS Boulangerie Lecomte",
        "garantie_description": "Garantie DDE pro + PE applicable. Réserve sur étendue des pertes d'exploitation.",
        "conclusion_expert": "",
    },
}

if __name__ == "__main__":
    init_db()
    print("Création des dossiers de test…")
    insert("2025-UF-A3F2C1B0", "Clôturé",   D4, created_offset_days=145)
    insert("2025-UF-B7E9D4A2", "En cours",  D2, created_offset_days=90)
    insert("2025-UF-C1F8E3D5", "Clôturé",   D1, created_offset_days=110)
    insert("2026-UF-D4A1B2C3", "À traiter", D3, created_offset_days=55)
    insert("2026-UF-E9C3F7A1", "En cours",  D5, created_offset_days=26)
    print("✅ 5 dossiers créés avec succès.")
