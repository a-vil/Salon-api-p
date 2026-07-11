from pydantic import BaseModel, ConfigDict, Field


class RecompensaBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    puntos_requeridos: int = Field(gt=0)

class RecompensaCreate(RecompensaBase):
    pass

class RecompensaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    puntos_requeridos: int | None = Field(default=None, gt=0)

class RecompensaOut(RecompensaBase):
    id: int
    activo: bool

    model_config = ConfigDict(from_attributes=True)
