from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CanjeCreate(BaseModel):
    recompensa_id: int
    cantidad: int = Field(default=1, gt=0)


class CanjeOut(BaseModel):
    id: int
    cliente_id: int
    recompensa_id: int
    recompensa_nombre: str
    cantidad: int = Field(gt=0)
    puntos_usados: int = Field(gt=0)
    saldo_puntos_actual: int
    fecha_canje: datetime
    estado: str

    model_config = ConfigDict(from_attributes=True)
