from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db import get_db
from app.models.admin_audit import AuditoriaAdmin
from app.models.user import Usuario
from app.schemas.admin_audit import AuditoriaAdminOut

router = APIRouter(prefix="/auditoria-admin", tags=["Auditoria Admin"])


@router.get("", response_model=list[AuditoriaAdminOut])
def listar_auditoria_admin(
    accion: str | None = None,
    entidad: str | None = None,
    admin_user_id: int | None = None,
    entidad_id: int | None = None,
    limite: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    limite = max(1, min(limite, 500))

    query = db.query(AuditoriaAdmin)

    if accion:
        query = query.filter(AuditoriaAdmin.accion == accion)
    if entidad:
        query = query.filter(AuditoriaAdmin.entidad == entidad)
    if admin_user_id is not None:
        query = query.filter(AuditoriaAdmin.admin_user_id == admin_user_id)
    if entidad_id is not None:
        query = query.filter(AuditoriaAdmin.entidad_id == entidad_id)

    return (
        query.order_by(AuditoriaAdmin.created_at.desc())
        .limit(limite)
        .all()
    )
