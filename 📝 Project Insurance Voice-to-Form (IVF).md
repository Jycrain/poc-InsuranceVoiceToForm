# 📝 Project: Insurance Voice-to-Form (IVF)  
## 🎯 Vision du Projet  
Développer une solution de **Speech-to-Text (STT)** pour assister les téléconseillers en assurance. Le système doit transcrire la voix en temps réel (ou via fichier) et extraire intelligemment des données structurées pour pré-remplir un formulaire d'expertise sinistre.  
## 🛠 Stack Technique  
* **IA Dev :** Claude Code  
* **Langage :** Python 3.10+  
* **Moteur STT :** NVIDIA NeMo (Modèle **Parakeet** - Open Source)  
* **Traitement NLP :** Spacy ou LLM léger (Type Mistral/Llama via API locale)  
* **Architecture :** Clean Architecture / SOLID  
  
## 🏛 Principes de Conception  
## 1. KISS (Keep It Simple, Stupid)  
* Pas de base de données complexe pour la V1 : utilisation de fichiers JSON/Pydantic pour les schémas de données.  
* Interface utilisateur minimale : FastAPI avec une documentation Swagger pour tester les endpoints.  
* Un script de pipeline unique pour l'enchaînement STT -> NLP.  
## 2. SOLID  
* **S (Single Responsibility) :** Un module pour l'audio, un pour la transcription, un pour le parsing de données.  
* **O (Open/Closed) :** L'interface de transcription doit permettre d'ajouter de nouveaux modèles (ex: passer de Parakeet à Whisper) sans modifier la logique métier.  
* **L (Liskov Substitution) :** Toutes les implémentations de STTProvider doivent être interchangeables.  
* **I (Interface Segregation) :** Ne pas forcer le moteur STT à connaître la structure du formulaire d'assurance.  
* **D (Dependency Inversion) :** Dépendre d'abstractions (interfaces) et non d'implémentations concrètes.  
  
## 📂 Structure du Projet (Arborescence)  
Plaintext  
  
```
/
├── src/
│   ├── core/               # Logique métier & Interfaces (Abstractions)
│   │   ├── interfaces.py   # Definitions des classes abstraites (STT, Parser)
│   │   └── models.py       # Modèles Pydantic (Formulaire Sinistre)
│   ├── providers/          # Implémentations concrètes
│   │   ├── stt_parakeet.py # Moteur NVIDIA NeMo Parakeet
│   │   └── nlp_extractor.py# Logique d'extraction des champs
│   ├── api/                # Points d'entrée (FastAPI)
│   └── utils/              # Traitement audio (resampling, wav conversion)
├── tests/                  # Tests unitaires et d'intégration
├── pyproject.toml          # Dépendances (Poetry/Pip)
└── README.md

```
  
## 📋 Spécifications du Formulaire d'Expertise  
Le système doit extraire en priorité les champs suivants de la transcription :  
* date_sinistre: Date mentionnée par l'assuré.  
* type_sinistre: (Dégât des eaux, Incendie, Vol, Bris de glace).  
* localisation: Pièce concernée ou adresse.  
* tiers_implique: Présence ou non d'une autre personne responsable/victime.  
* description_courte: Résumé synthétique du dommage.  
  
## 🚀 Roadmap pour Claude Code  
1. **Phase 1 : Fondations.** Créer les interfaces STTInterface et les modèles Pydantic pour le formulaire.  
2. **Phase 2 : Moteur STT.** Implémenter ParakeetTranscriber en utilisant nemo_toolkit.  
3. **Phase 3 : Extraction NLP.** Créer la logique de mapping entre le texte brut et les champs du formulaire.  
4. **Phase 4 : API & Test.** Exposer un endpoint /upload-audio qui retourne le formulaire rempli.  
  
## 🧪 Exemple de test  
**Input :** *"Le 24 février, j'ai eu une fuite d'eau dans ma cuisine à cause du lave-vaisselle."* **Output attendu :**  
JSON  
  
```
{
  "date": "2026-02-24",
  "type": "Dégât des eaux",
  "piece": "Cuisine",
  "cause": "Lave-vaisselle"
}

```
