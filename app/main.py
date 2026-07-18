from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import fastapi_swagger_dark as fsd

from app.core.config import settings
from app.routers.admin_audit import router as admin_audit_router
from app.routers.clients import router as clients_router
from app.routers.points import router as points_router
from app.routers.redeems import router as redeems_router
from app.routers.rewards import router as rewards_router
from app.routers.auth import router as auth_router

app = FastAPI(
    title="Sistema de Fidelizacion - API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients_router)
app.include_router(admin_audit_router)
app.include_router(points_router)
app.include_router(redeems_router)
app.include_router(rewards_router)
app.include_router(auth_router)

if settings.enable_docs:
    docs_router = APIRouter()
    fsd.install(docs_router)
    app.include_router(docs_router)


@app.get("/")
def health():
    return {"status": "ok"}
