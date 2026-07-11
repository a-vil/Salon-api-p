from datetime import datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.session_auth import get_session_from_token, revoke_session, touch_session
from app.db import get_db
from app.models.session import Sesion
from app.models.user import Usuario


def _extract_session_token(request: Request) -> str | None:
    cookie_token = request.cookies.get(settings.session_cookie_name)
    if cookie_token:
        return cookie_token

    authorization = request.headers.get("authorization")
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def get_current_session(
    request: Request,
    db: Session = Depends(get_db),
) -> Sesion:
    session_token = _extract_session_token(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Sesion no autenticada")

    sesion = get_session_from_token(db, session_token)
    if not sesion:
        raise HTTPException(status_code=401, detail="Sesion invalida")

    now = datetime.utcnow()
    if sesion.estado != "activa":
        raise HTTPException(status_code=401, detail="Sesion expirada o invalidada")
    if sesion.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Sesion expirada o invalidada")
    if sesion.expires_at <= now:
        revoke_session(db, sesion, estado="expirada")
        db.commit()
        raise HTTPException(status_code=401, detail="Sesion expirada o invalidada")

    session_touched = touch_session(db, sesion, request)
    if session_touched:
        db.commit()
        db.refresh(sesion)
    return sesion


def get_current_user(
    current_session: Sesion = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == current_session.user_id).first()
    if not usuario:
        revoke_session(db, current_session)
        db.commit()
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if not usuario.activo:
        revoke_session(db, current_session)
        db.commit()
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    return usuario


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return current_user


def require_cliente(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol != "cliente":
        raise HTTPException(status_code=403, detail="Acceso restringido a clientes")
    if current_user.cliente_id is None:
        raise HTTPException(status_code=403, detail="Usuario cliente sin perfil asociado")
    return current_user
