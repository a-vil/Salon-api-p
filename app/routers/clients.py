from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.audit import log_admin_action
from app.core.dependencies import require_admin, require_cliente
from app.core.security import normalize_identifier
from app.core.session_auth import revoke_active_sessions_for_user
from app.db import get_db
from app.models.client import Cliente
from app.models.points_account import CuentaPuntos
from app.models.user import Usuario
from app.schemas.client import ClienteOut, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=list[ClienteOut])
def listar_clientes(
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    query = db.query(Cliente)

    if not incluir_inactivos:
        query = query.filter(Cliente.activo.is_(True))

    return query.all()


@router.get("/{cliente_id:int}", response_model=ClienteOut)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/mi-cuenta", response_model=ClienteOut)
def mi_cuenta(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_cliente),
):
    cliente = db.query(Cliente).filter(Cliente.id == current_user.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.patch("/{cliente_id:int}", response_model=ClienteOut)
def actualizar_parcial_cliente(
    cliente_id: int,
    payload: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "correo" in data and data["correo"] is not None:
        data["correo"] = data["correo"].lower()
    if "celular" in data and data["celular"] is not None:
        data["celular"] = normalize_identifier(data["celular"])

    for key, value in data.items():
        setattr(cliente, key, value)
        if cliente.usuario and key in {"correo", "celular"}:
            setattr(cliente.usuario, key, value)

    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="actualizar_cliente",
            entity="cliente",
            entity_id=cliente.id,
            detail={"campos_actualizados": data},
        )
        db.commit()
        db.refresh(cliente)
        return cliente
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un cliente con el mismo dni, correo o celular",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo actualizar el cliente")


@router.patch("/{cliente_id:int}/desactivar", response_model=ClienteOut)
def desactivar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if not cliente.activo:
        raise HTTPException(status_code=409, detail="Cliente ya se encuentra inactivo")

    cliente.activo = False
    fecha_desactivacion = datetime.utcnow()
    cliente.fecha_desactivacion = fecha_desactivacion
    if cliente.cuenta_puntos:
        cliente.cuenta_puntos.estado = "inactiva"
    if cliente.usuario:
        cliente.usuario.activo = False
        cliente.usuario.token_version += 1
        revoke_active_sessions_for_user(db, cliente.usuario.id)
    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="desactivar_cliente",
            entity="cliente",
            entity_id=cliente.id,
            detail={"fecha_desactivacion": fecha_desactivacion.isoformat()},
        )
        db.commit()
        db.refresh(cliente)
        return cliente
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo desactivar el cliente")


@router.patch("/{cliente_id:int}/activar", response_model=ClienteOut)
def activar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if cliente.activo:
        raise HTTPException(status_code=409, detail="Cliente ya se encuentra activo")

    cliente.activo = True
    cliente.fecha_desactivacion = None
    if cliente.cuenta_puntos:
        cliente.cuenta_puntos.estado = "activa"
    if cliente.usuario:
        cliente.usuario.activo = True
    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="activar_cliente",
            entity="cliente",
            entity_id=cliente.id,
            detail={"fecha_desactivacion": None},
        )
        db.commit()
        db.refresh(cliente)
        return cliente
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo activar el cliente")
