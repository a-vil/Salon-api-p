from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from decimal import Decimal


class ClientePuntosOut(BaseModel):
    cliente_id: int
    nombre: str | None = None
    apellido: str | None = None
    activo_cliente: bool
    fecha_desactivacion: datetime | None = None
    saldo_puntos: int
    estado_cuenta: str

    model_config = ConfigDict(from_attributes=True)

class AcumularPuntosIn(BaseModel):
    cliente_id: int
    monto_compra: float = Field(gt=0)
    descripcion: str | None = None


class AcumularPuntosOut(BaseModel):
    movimiento_id: int
    cliente_id: int
    puntos_ganados: int
    saldo_puntos: int
    monto_compra: float
    descripcion: str | None = None


class EliminarMovimientoOut(BaseModel):
    movimiento_id: int
    cliente_id: int
    saldo_puntos: int
    detail: str

class MovimientoPuntosOut(BaseModel):
    id: int
    tipo: str
    puntos: int
    monto_compra: Decimal | None = None
    descripcion: str | None = None
    fecha_movimiento: datetime

    model_config = ConfigDict(from_attributes=True)

class HistorialPuntosOut(BaseModel):
    cliente_id: int
    activo_cliente: bool
    fecha_desactivacion: datetime | None = None
    saldo_puntos: int
    movimientos: list[MovimientoPuntosOut]


class MovimientoAdminOut(BaseModel):
    id: int
    cliente_id: int
    nombre: str | None = None
    apellido: str | None = None
    tipo: str
    puntos: int
    monto_compra: Decimal | None = None
    descripcion: str | None = None
    fecha_movimiento: datetime


class HistorialGlobalOut(BaseModel):
    movimientos: list[MovimientoAdminOut]
