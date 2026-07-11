from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioOut(BaseModel):
    id: int
    correo: EmailStr | None = None
    celular: str | None = None
    rol: str
    activo: bool
    cliente_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
