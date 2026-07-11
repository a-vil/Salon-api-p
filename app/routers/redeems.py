from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.audit import log_admin_action
from app.core.dependencies import require_admin, require_cliente
from app.db import get_db
from app.models.client import Cliente
from app.models.points_account import CuentaPuntos
from app.models.points_movement import MovimientoPuntos
from app.models.redeem import Canje
from app.models.reward import Recompensa
from app.models.user import Usuario
from app.schemas.redeem import CanjeCreate, CanjeOut

router = APIRouter(prefix="/canjes", tags=["Canjes"])


def _build_canje_out(
    *,
    canje: Canje,
    cliente_id: int,
    recompensa_nombre: str,
    saldo_puntos_actual: int,
) -> CanjeOut:
    return CanjeOut(
        id=canje.id,
        cliente_id=cliente_id,
        recompensa_id=canje.recompensa_id,
        recompensa_nombre=recompensa_nombre,
        cantidad=canje.cantidad,
        puntos_usados=canje.puntos_usados,
        saldo_puntos_actual=saldo_puntos_actual,
        fecha_canje=canje.fecha_canje,
        estado=canje.estado,
    )


@router.post("", response_model=CanjeOut)
def solicitar_canje(
    payload: CanjeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_cliente),
):
    cliente_id = current_user.cliente_id
    if cliente_id is None:
        raise HTTPException(status_code=403, detail="Usuario cliente sin perfil asociado")

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not cliente.activo:
        raise HTTPException(status_code=409, detail="El cliente se encuentra inactivo")

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.cliente_id == cliente.id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")
    if cuenta.estado != "activa":
        raise HTTPException(status_code=409, detail="La cuenta de puntos no esta activa")

    recompensa = db.query(Recompensa).filter(Recompensa.id == payload.recompensa_id).first()
    if not recompensa:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")
    if not recompensa.activo:
        raise HTTPException(status_code=409, detail="La recompensa no se encuentra disponible")

    canje_pendiente = (
        db.query(Canje)
        .filter(Canje.cuenta_id == cuenta.id, Canje.estado == "pendiente")
        .first()
    )
    if canje_pendiente:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un canje pendiente para este cliente. Espera confirmacion o cancelacion antes de solicitar otro.",
        )

    puntos_totales = recompensa.puntos_requeridos * payload.cantidad
    if cuenta.saldo_puntos < puntos_totales:
        raise HTTPException(
            status_code=409,
            detail="El cliente no tiene puntos suficientes para esta solicitud de canje",
        )

    canje = Canje(
        cuenta_id=cuenta.id,
        recompensa_id=recompensa.id,
        cantidad=payload.cantidad,
        puntos_usados=puntos_totales,
        estado="pendiente",
    )
    db.add(canje)

    try:
        db.commit()
        db.refresh(canje)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un canje pendiente para este cliente. Espera confirmacion o cancelacion antes de solicitar otro.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo registrar la solicitud de canje")

    return _build_canje_out(
        canje=canje,
        cliente_id=cliente.id,
        recompensa_nombre=recompensa.nombre,
        saldo_puntos_actual=cuenta.saldo_puntos,
    )


@router.get("", response_model=list[CanjeOut])
def listar_canjes(
    estado: str | None = None,
    cliente_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    query = db.query(Canje).join(CuentaPuntos).join(Recompensa)

    if estado:
        query = query.filter(Canje.estado == estado)
    if cliente_id:
        query = query.filter(CuentaPuntos.cliente_id == cliente_id)

    canjes = query.order_by(Canje.fecha_canje.desc()).all()

    resultados: list[CanjeOut] = []
    for canje in canjes:
        cuenta = canje.cuenta
        recompensa = canje.recompensa
        if cuenta is None or recompensa is None:
            raise HTTPException(status_code=500, detail="Canje con relaciones incompletas")

        resultados.append(
            _build_canje_out(
                canje=canje,
                cliente_id=cuenta.cliente_id,
                recompensa_nombre=recompensa.nombre,
                saldo_puntos_actual=cuenta.saldo_puntos,
            )
        )

    return resultados


@router.get("/mis-canjes", response_model=list[CanjeOut])
def listar_mis_canjes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_cliente),
):
    cliente_id = current_user.cliente_id
    if cliente_id is None:
        raise HTTPException(status_code=403, detail="Usuario cliente sin perfil asociado")

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.cliente_id == cliente_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")

    canjes = (
        db.query(Canje)
        .join(Recompensa)
        .filter(Canje.cuenta_id == cuenta.id)
        .order_by(Canje.fecha_canje.desc())
        .all()
    )

    resultados: list[CanjeOut] = []
    for canje in canjes:
        recompensa = canje.recompensa
        if recompensa is None:
            raise HTTPException(status_code=500, detail="Canje con recompensa incompleta")

        resultados.append(
            _build_canje_out(
                canje=canje,
                cliente_id=cliente_id,
                recompensa_nombre=recompensa.nombre,
                saldo_puntos_actual=cuenta.saldo_puntos,
            )
        )

    return resultados


@router.patch("/{canje_id}/confirmar", response_model=CanjeOut)
def confirmar_canje(
    canje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    canje = db.query(Canje).filter(Canje.id == canje_id).first()
    if not canje:
        raise HTTPException(status_code=404, detail="Canje no encontrado")
    if canje.estado != "pendiente":
        raise HTTPException(status_code=409, detail="Solo se pueden confirmar canjes pendientes")

    cuenta = canje.cuenta
    recompensa = canje.recompensa
    if cuenta is None or recompensa is None:
        raise HTTPException(status_code=500, detail="Canje con relaciones incompletas")

    cliente = cuenta.cliente
    if cliente is None:
        raise HTTPException(status_code=500, detail="Cuenta sin cliente asociado")

    if not cliente.activo:
        raise HTTPException(status_code=409, detail="No se puede confirmar un canje para un cliente inactivo")
    if cuenta.estado != "activa":
        raise HTTPException(status_code=409, detail="La cuenta de puntos no esta activa")
    if cuenta.saldo_puntos < canje.puntos_usados:
        raise HTTPException(
            status_code=409,
            detail="El cliente ya no tiene puntos suficientes para confirmar este canje",
        )

    saldo_result = cast(
        CursorResult,
        db.execute(
        update(CuentaPuntos)
        .where(
            CuentaPuntos.id == cuenta.id,
            CuentaPuntos.estado == "activa",
            CuentaPuntos.saldo_puntos >= canje.puntos_usados,
        )
        .values(saldo_puntos=CuentaPuntos.saldo_puntos - canje.puntos_usados)
        ),
    )
    saldo_rowcount = saldo_result.rowcount or 0
    if saldo_rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo confirmar el canje porque el saldo o el estado de la cuenta cambiaron",
        )

    canje_result = cast(
        CursorResult,
        db.execute(
        update(Canje)
        .where(Canje.id == canje.id, Canje.estado == "pendiente")
        .values(estado="confirmado")
        ),
    )
    canje_rowcount = canje_result.rowcount or 0
    if canje_rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El canje ya no se encuentra pendiente y no puede confirmarse",
        )

    movimiento = MovimientoPuntos(
        cuenta_id=cuenta.id,
        tipo="canje",
        puntos=-canje.puntos_usados,
        descripcion=f"Canje confirmado: {recompensa.nombre} x{canje.cantidad}",
    )
    db.add(movimiento)

    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="confirmar_canje",
            entity="canje",
            entity_id=canje.id,
            detail={
                "cliente_id": cliente.id,
                "recompensa_id": recompensa.id,
                "cantidad": canje.cantidad,
                "puntos_usados": canje.puntos_usados,
            },
        )
        db.commit()
        db.refresh(canje)
        db.refresh(cuenta)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo confirmar el canje")

    return _build_canje_out(
        canje=canje,
        cliente_id=cliente.id,
        recompensa_nombre=recompensa.nombre,
        saldo_puntos_actual=cuenta.saldo_puntos,
    )


@router.patch("/{canje_id}/cancelar", response_model=CanjeOut)
def cancelar_canje(
    canje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    canje = db.query(Canje).filter(Canje.id == canje_id).first()
    if not canje:
        raise HTTPException(status_code=404, detail="Canje no encontrado")
    if canje.estado != "pendiente":
        raise HTTPException(status_code=409, detail="Solo se pueden cancelar canjes pendientes")

    canje_result = cast(
        CursorResult,
        db.execute(
        update(Canje)
        .where(Canje.id == canje.id, Canje.estado == "pendiente")
        .values(estado="cancelado")
        ),
    )
    canje_rowcount = canje_result.rowcount or 0
    if canje_rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El canje ya no se encuentra pendiente y no puede cancelarse",
        )

    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="cancelar_canje",
            entity="canje",
            entity_id=canje.id,
            detail={
                "cliente_id": canje.cuenta.cliente_id if canje.cuenta else None,
                "recompensa_id": canje.recompensa_id,
                "cantidad": canje.cantidad,
                "puntos_usados": canje.puntos_usados,
            },
        )
        db.commit()
        db.refresh(canje)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo cancelar el canje")

    cuenta = canje.cuenta
    recompensa = canje.recompensa
    if cuenta is None or recompensa is None:
        raise HTTPException(status_code=500, detail="Canje con relaciones incompletas")

    return _build_canje_out(
        canje=canje,
        cliente_id=cuenta.cliente_id,
        recompensa_nombre=recompensa.nombre,
        saldo_puntos_actual=cuenta.saldo_puntos,
    )
