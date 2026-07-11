import hashlib
from datetime import datetime, timedelta
from secrets import token_urlsafe

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.session import Sesion
from app.models.user import Usuario


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_session_token() -> str:
    return token_urlsafe(48)


def _extract_request_metadata(request: Request) -> tuple[str | None, str | None]:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return client_ip, user_agent


def revoke_active_sessions_for_user(db: Session, user_id: int) -> None:
    now = datetime.utcnow()
    (
        db.query(Sesion)
        .filter(Sesion.user_id == user_id, Sesion.estado == "activa")
        .update(
            {
                Sesion.estado: "revocada",
                Sesion.revoked_at: now,
                Sesion.updated_at: now,
            },
            synchronize_session=False,
        )
    )


def create_session_for_user(db: Session, user: Usuario, request: Request) -> tuple[str, Sesion]:
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=settings.session_expire_minutes)
    session_token = generate_session_token()
    session_token_hash = hash_session_token(session_token)
    client_ip, user_agent = _extract_request_metadata(request)

    revoke_active_sessions_for_user(db, user.id)

    sesion = Sesion(
        session_token_hash=session_token_hash,
        user_id=user.id,
        estado="activa",
        ip_creacion=client_ip,
        user_agent_creacion=user_agent,
        ip_ultima_actividad=client_ip,
        user_agent_ultima_actividad=user_agent,
        expires_at=expires_at,
        last_seen_at=now,
    )
    db.add(sesion)
    db.flush()
    return session_token, sesion


def get_session_from_token(db: Session, session_token: str) -> Sesion | None:
    return (
        db.query(Sesion)
        .filter(Sesion.session_token_hash == hash_session_token(session_token))
        .first()
    )


def revoke_session(db: Session, sesion: Sesion, *, estado: str = "revocada") -> None:
    now = datetime.utcnow()
    sesion.estado = estado
    sesion.revoked_at = now
    sesion.updated_at = now


def touch_session(db: Session, sesion: Sesion, request: Request) -> bool:
    now = datetime.utcnow()
    if sesion.last_seen_at and (now - sesion.last_seen_at).total_seconds() < settings.session_touch_interval_seconds:
        return False

    client_ip, user_agent = _extract_request_metadata(request)
    sesion.last_seen_at = now
    sesion.ip_ultima_actividad = client_ip
    sesion.user_agent_ultima_actividad = user_agent
    sesion.updated_at = now
    db.flush()
    return True
