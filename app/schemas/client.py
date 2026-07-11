from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class ClienteBase(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    dni: str | None = None
    celular: str | None = None
    correo: EmailStr | None = None
    fecha_naci: date | None = None

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, value: str | None):
        if value is None:
            return value
        if not value.isdigit() or len(value) != 8:
            raise ValueError("El DNI debe tener exactamente 8 digitos")
        return value

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, value: str | None):
        if value is None:
            return value
        if not value.isdigit() or len(value) != 9:
            raise ValueError("El celular debe tener exactamente 9 digitos")
        return value

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    pass

class ClienteOut(ClienteBase):
    id: int
    activo: bool
    fecha_desactivacion: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
