"""
Point d'entrée FastAPI.
Lance avec : uvicorn src.api.app:app --reload
"""
import contextlib
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.routes_dossiers import router as dossiers_router
from src.db.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    init_db()
    yield


app = FastAPI(
    title="Insurance Voice-to-Form (IVF)",
    description=(
        "Pipeline Speech-to-Text → NLP pour pré-remplir automatiquement "
        "un formulaire d'expertise sinistre à partir de la voix d'un assuré."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")
app.include_router(dossiers_router, prefix="/api/v1")

# Serve frontend UI
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse(
        _static_dir / "index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )
