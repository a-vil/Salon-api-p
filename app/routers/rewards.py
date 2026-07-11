from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.audit import log_admin_action
from app.core.dependencies import get_current_user, require_admin
from app.db import get_db
from app.models.reward import Recompensa
from app.models.user import Usuario
from app.schemas.reward import RecompensaCreate, RecompensaOut, RecompensaUpdate

router = APIRouter(prefix="/recompensas", tags=["Recompensas"])


@router.post("", response_model=RecompensaOut)
def crear_recompensa(
    payload: RecompensaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    recompensa = Recompensa(**payload.model_dump())
    db.add(recompensa)
    try:
        db.flush()
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="crear_recompensa",
            entity="recompensa",
            entity_id=recompensa.id,
            detail=payload.model_dump(),
        )
        db.commit()
        db.refresh(recompensa)
        return recompensa
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo crear la recompensa")


@router.get("", response_model=list[RecompensaOut])
def listar_recompensas(
    incluir_inactivas: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(Recompensa)

    if current_user.rol != "admin" or not incluir_inactivas:
        query = query.filter(Recompensa.activo.is_(True))

    return query.all()


@router.get("/{recompensa_id}", response_model=RecompensaOut)
def obtener_recompensa(
    recompensa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    recompensa = db.query(Recompensa).filter(Recompensa.id == recompensa_id).first()
    if not recompensa:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")
    if current_user.rol != "admin" and not recompensa.activo:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")
    return recompensa


@router.patch("/{recompensa_id}", response_model=RecompensaOut)
def actualizar_recompensa(
    recompensa_id: int,
    payload: RecompensaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    recompensa = db.query(Recompensa).filter(Recompensa.id == recompensa_id).first()
    if not recompensa:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(recompensa, key, value)

    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="actualizar_recompensa",
            entity="recompensa",
            entity_id=recompensa.id,
            detail={"campos_actualizados": data},
        )
        db.commit()
        db.refresh(recompensa)
        return recompensa
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo actualizar la recompensa")


@router.patch("/{recompensa_id}/desactivar", response_model=RecompensaOut)
def desactivar_recompensa(
    recompensa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    recompensa = db.query(Recompensa).filter(Recompensa.id == recompensa_id).first()
    if not recompensa:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")

    if not recompensa.activo:
        raise HTTPException(status_code=409, detail="Recompensa ya se encuentra inactiva")

    recompensa.activo = False
    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="desactivar_recompensa",
            entity="recompensa",
            entity_id=recompensa.id,
            detail={"activo": False},
        )
        db.commit()
        db.refresh(recompensa)
        return recompensa
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo desactivar la recompensa")


@router.patch("/{recompensa_id}/activar", response_model=RecompensaOut)
def activar_recompensa(
    recompensa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    recompensa = db.query(Recompensa).filter(Recompensa.id == recompensa_id).first()
    if not recompensa:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")

    if recompensa.activo:
        raise HTTPException(status_code=409, detail="Recompensa ya se encuentra activa")

    recompensa.activo = True
    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="activar_recompensa",
            entity="recompensa",
            entity_id=recompensa.id,
            detail={"activo": True},
        )
        db.commit()
        db.refresh(recompensa)
        return recompensa
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo activar la recompensa")
