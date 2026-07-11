import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.admin_audit import AuditoriaAdmin
from app.models.user import Usuario


def log_admin_action(
    *,
    db: Session,
    admin_user: Usuario,
    action: str,
    entity: str,
    entity_id: int,
    detail: dict[str, Any],
) -> None:
    admin_identifier = admin_user.correo or admin_user.celular or f"admin:{admin_user.id}"
    audit = AuditoriaAdmin(
        admin_user_id=admin_user.id,
        admin_identificador=admin_identifier,
        accion=action,
        entidad=entity,
        entidad_id=entity_id,
        detalle=json.dumps(detail, ensure_ascii=False, sort_keys=True),
    )
    db.add(audit)
