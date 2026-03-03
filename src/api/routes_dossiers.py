"""
Endpoints CRUD pour les dossiers d'expertise.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from src.db import database

router = APIRouter(prefix="/dossiers", tags=["Dossiers"])


@router.get("", summary="Lister tous les dossiers")
async def list_dossiers() -> list[dict]:
    return database.list_dossiers()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Créer un nouveau dossier")
async def create_dossier() -> dict:
    return database.create_dossier()


@router.get("/{dossier_id}", summary="Récupérer un dossier")
async def get_dossier(dossier_id: str) -> dict:
    d = database.get_dossier(dossier_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    return d


@router.put("/{dossier_id}", summary="Mettre à jour un dossier")
async def update_dossier(dossier_id: str, payload: dict[str, Any]) -> dict:
    d = database.update_dossier(dossier_id, payload)
    if d is None:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    return d


@router.delete("/{dossier_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un dossier")
async def delete_dossier(dossier_id: str) -> None:
    if database.get_dossier(dossier_id) is None:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    database.delete_dossier(dossier_id)
