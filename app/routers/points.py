from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.audit import log_admin_action
from app.core.dependencies import require_admin, require_cliente
from app.db import get_db
from app.models.client import Cliente
from app.models.points_account import CuentaPuntos
from app.models.points_movement import MovimientoPuntos
from app.models.user import Usuario
from app.schemas.points import (
    AcumularPuntosIn,
    AcumularPuntosOut,
    ClientePuntosOut,
    EliminarMovimientoOut,
    HistorialGlobalOut,
    HistorialPuntosOut,
    MovimientoAdminOut,
    MovimientoPuntosOut,
)

router = APIRouter(prefix="/puntos", tags=["Puntos"])


@router.get("/movimientos", response_model=HistorialGlobalOut)
def obtener_historial_global(
    cliente_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    query = (
        db.query(MovimientoPuntos, CuentaPuntos, Cliente)
        .join(CuentaPuntos, MovimientoPuntos.cuenta_id == CuentaPuntos.id)
        .join(Cliente, CuentaPuntos.cliente_id == Cliente.id)
    )

    if cliente_id is not None:
        query = query.filter(Cliente.id == cliente_id)

    resultados = (
        query.order_by(MovimientoPuntos.fecha_movimiento.desc())
        .all()
    )

    return HistorialGlobalOut(
        movimientos=[
            MovimientoAdminOut(
                id=movimiento.id,
                cliente_id=cliente.id,
                nombre=cliente.nombre,
                apellido=cliente.apellido,
                tipo=movimiento.tipo,
                puntos=movimiento.puntos,
                monto_compra=movimiento.monto_compra,
                descripcion=movimiento.descripcion,
                fecha_movimiento=movimiento.fecha_movimiento,
            )
            for movimiento, cuenta, cliente in resultados
        ]
    )


@router.get("/clientes/{cliente_id:int}", response_model=ClientePuntosOut)
def obtener_puntos_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.cliente_id == cliente_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")

    return ClientePuntosOut(
        cliente_id=cliente.id,
        nombre=cliente.nombre,
        apellido=cliente.apellido,
        activo_cliente=cliente.activo,
        fecha_desactivacion=cliente.fecha_desactivacion,
        saldo_puntos=cuenta.saldo_puntos,
        estado_cuenta=cuenta.estado,
    )


@router.get("/mis-puntos", response_model=ClientePuntosOut)
def obtener_mis_puntos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_cliente),
):
    cliente = db.query(Cliente).filter(Cliente.id == current_user.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.cliente_id == cliente.id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")

    return ClientePuntosOut(
        cliente_id=cliente.id,
        nombre=cliente.nombre,
        apellido=cliente.apellido,
        activo_cliente=cliente.activo,
        fecha_desactivacion=cliente.fecha_desactivacion,
        saldo_puntos=cuenta.saldo_puntos,
        estado_cuenta=cuenta.estado,
    )


@router.post("/acumular", response_model=AcumularPuntosOut)
def acumular_puntos(
    payload: AcumularPuntosIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id == payload.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not cliente.activo:
        raise HTTPException(status_code=409, detail="No se pueden acumular puntos para un cliente inactivo")

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.cliente_id == payload.cliente_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")
    if cuenta.estado != "activa":
        raise HTTPException(status_code=409, detail="La cuenta de puntos no esta activa")

    puntos_ganados = int(payload.monto_compra // 10)

    cuenta.saldo_puntos += puntos_ganados

    movimiento = MovimientoPuntos(
        cuenta_id=cuenta.id,
        tipo="acumulacion",
        puntos=puntos_ganados,
        monto_compra=payload.monto_compra,
        descripcion=payload.descripcion,
    )

    db.add(movimiento)
    try:
        db.flush()
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="acumular_puntos",
            entity="movimiento_puntos",
            entity_id=movimiento.id,
            detail={
                "cliente_id": cliente.id,
                "cuenta_id": cuenta.id,
                "puntos_ganados": puntos_ganados,
                "monto_compra": payload.monto_compra,
                "descripcion": payload.descripcion,
            },
        )
        db.commit()
        db.refresh(movimiento)
        db.refresh(cuenta)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudieron acumular los puntos")

    return AcumularPuntosOut(
        movimiento_id=movimiento.id,
        cliente_id=cliente.id,
        puntos_ganados=puntos_ganados,
        saldo_puntos=cuenta.saldo_puntos,
        monto_compra=payload.monto_compra,
        descripcion=payload.descripcion,
    )


@router.delete("/movimientos/{movimiento_id:int}", response_model=EliminarMovimientoOut)
def eliminar_movimiento(
    movimiento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    movimiento = db.query(MovimientoPuntos).filter(MovimientoPuntos.id == movimiento_id).first()
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")

    if movimiento.tipo != "acumulacion":
        raise HTTPException(
            status_code=409,
            detail="Solo se pueden revertir movimientos de acumulacion registrados por error.",
        )

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.id == movimiento.cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")

    cliente = db.query(Cliente).filter(Cliente.id == cuenta.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if cuenta.saldo_puntos < movimiento.puntos:
        raise HTTPException(
            status_code=409,
            detail="No se puede revertir el movimiento porque el saldo actual es insuficiente.",
        )

    cuenta.saldo_puntos -= movimiento.puntos
    db.delete(movimiento)

    try:
        log_admin_action(
            db=db,
            admin_user=current_user,
            action="revertir_movimiento",
            entity="movimiento_puntos",
            entity_id=movimiento_id,
            detail={
                "cliente_id": cliente.id,
                "cuenta_id": cuenta.id,
                "puntos_revertidos": movimiento.puntos,
                "saldo_resultante": cuenta.saldo_puntos,
            },
        )
        db.commit()
        db.refresh(cuenta)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo revertir el movimiento")

    return EliminarMovimientoOut(
        movimiento_id=movimiento_id,
        cliente_id=cliente.id,
        saldo_puntos=cuenta.saldo_puntos,
        detail="Movimiento revertido correctamente.",
    )

@router.get("/clientes/{cliente_id:int}/movimientos", response_model=HistorialPuntosOut)
def obtener_historial_puntos(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.cliente_id == cliente_id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")

    movimientos = (
        db.query(MovimientoPuntos)
        .filter(MovimientoPuntos.cuenta_id == cuenta.id)
        .order_by(MovimientoPuntos.fecha_movimiento.desc())
        .all()
    )

    return HistorialPuntosOut(
        cliente_id=cliente.id,
        activo_cliente=cliente.activo,
        fecha_desactivacion=cliente.fecha_desactivacion,
        saldo_puntos=cuenta.saldo_puntos,
        movimientos=[
            MovimientoPuntosOut.model_validate(movimiento)
            for movimiento in movimientos
        ],
    )


@router.get("/mis-movimientos", response_model=HistorialPuntosOut)
def obtener_mis_movimientos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_cliente),
):
    cliente = db.query(Cliente).filter(Cliente.id == current_user.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    cuenta = db.query(CuentaPuntos).filter(CuentaPuntos.cliente_id == cliente.id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de puntos no encontrada")

    movimientos = (
        db.query(MovimientoPuntos)
        .filter(MovimientoPuntos.cuenta_id == cuenta.id)
        .order_by(MovimientoPuntos.fecha_movimiento.desc())
        .all()
    )

    return HistorialPuntosOut(
        cliente_id=cliente.id,
        activo_cliente=cliente.activo,
        fecha_desactivacion=cliente.fecha_desactivacion,
        saldo_puntos=cuenta.saldo_puntos,
        movimientos=[
            MovimientoPuntosOut.model_validate(movimiento)
            for movimiento in movimientos
        ],
    )
