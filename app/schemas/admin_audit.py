from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditoriaAdminOut(BaseModel):
    id: int
    admin_user_id: int
    admin_identificador: str
    accion: str
    entidad: str
    entidad_id: int
    detalle: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
