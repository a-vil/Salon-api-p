from threading import Lock
from datetime import datetime, timedelta, timezone
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_session, get_current_user
from app.core.security import (
    hash_password,
    normalize_identifier,
    verify_password,
)
from app.core.session_auth import create_session_for_user, revoke_session
from app.db import get_db
from app.models.client import Cliente
from app.models.points_account import CuentaPuntos
from app.models.session import Sesion
from app.models.user import Usuario
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UsuarioOut

router = APIRouter(prefix="/auth", tags=["Auth"])

FAILED_LOGIN_WINDOW_SECONDS = 15 * 60
FAILED_LOGIN_MAX_ATTEMPTS = 5
FAILED_LOGIN_BLOCK_SECONDS = 15 * 60

_failed_login_attempts: dict[str, list[float]] = {}
_failed_login_blocked_until: dict[str, float] = {}
_login_rate_limit_lock = Lock()


def _build_duplicate_detail() -> str:
    return (
        "Ya existe una cuenta registrada con los datos proporcionados. "
        "Recupera el acceso o contacta con administracion."
    )


def _build_login_failure_detail() -> str:
    return "Credenciales invalidas o acceso no disponible"


def _build_login_rate_limit_key(identifier: str, request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{identifier}"


def _cleanup_login_attempts(now: float) -> None:
    expired_attempts = [
        key
        for key, attempts in _failed_login_attempts.items()
        if not [attempt for attempt in attempts if now - attempt <= FAILED_LOGIN_WINDOW_SECONDS]
    ]
    for key in expired_attempts:
        _failed_login_attempts.pop(key, None)

    expired_blocks = [
        key
        for key, blocked_until in _failed_login_blocked_until.items()
        if blocked_until <= now
    ]
    for key in expired_blocks:
        _failed_login_blocked_until.pop(key, None)


def _ensure_login_not_blocked(key: str) -> None:
    now = time()
    with _login_rate_limit_lock:
        _cleanup_login_attempts(now)
        blocked_until = _failed_login_blocked_until.get(key)
        if blocked_until and blocked_until > now:
            retry_after_seconds = int(blocked_until - now)
            retry_after_minutes = max(1, (retry_after_seconds + 59) // 60)
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados intentos de inicio de sesion. Intenta nuevamente en {retry_after_minutes} minuto(s).",
            )


def _register_failed_login_attempt(key: str) -> None:
    now = time()
    with _login_rate_limit_lock:
        _cleanup_login_attempts(now)
        attempts = [
            attempt
            for attempt in _failed_login_attempts.get(key, [])
            if now - attempt <= FAILED_LOGIN_WINDOW_SECONDS
        ]
        attempts.append(now)
        _failed_login_attempts[key] = attempts
        if len(attempts) >= FAILED_LOGIN_MAX_ATTEMPTS:
            _failed_login_blocked_until[key] = now + FAILED_LOGIN_BLOCK_SECONDS


def _clear_failed_login_attempts(key: str) -> None:
    with _login_rate_limit_lock:
        _failed_login_attempts.pop(key, None)
        _failed_login_blocked_until.pop(key, None)


def _set_session_cookie(response: Response, session_token: str) -> None:
    max_age = settings.session_expire_minutes * 60
    expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=max_age,
        expires=expires,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        httponly=True,
    )


@router.post("/register", response_model=TokenResponse)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    correo = payload.correo.lower() if payload.correo else None
    celular = payload.celular
    dni = payload.dni

    if not correo and not celular:
        raise HTTPException(
            status_code=422,
            detail="Debe proporcionar al menos correo o celular",
        )

    user_filters = []
    if correo:
        user_filters.append(Usuario.correo == correo)
    if celular:
        user_filters.append(Usuario.celular == celular)

    existing_user = db.query(Usuario).filter(or_(*user_filters)).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=_build_duplicate_detail(),
        )

    cliente_filters = []
    if correo:
        cliente_filters.append(Cliente.correo == correo)
    if celular:
        cliente_filters.append(Cliente.celular == celular)

    existing_cliente = db.query(Cliente).filter(or_(*cliente_filters)).first()
    if existing_cliente:
        raise HTTPException(
            status_code=409,
            detail=_build_duplicate_detail(),
        )

    if dni:
        existing_dni_cliente = db.query(Cliente).filter(Cliente.dni == dni).first()
        if existing_dni_cliente:
            raise HTTPException(
                status_code=409,
                detail=_build_duplicate_detail(),
            )

    cliente = Cliente(
        nombre=payload.nombre,
        apellido=payload.apellido,
        dni=payload.dni,
        celular=celular,
        correo=correo,
        fecha_naci=payload.fecha_naci,
        activo=True,
        fecha_desactivacion=None,
    )
    db.add(cliente)

    try:
        db.flush()

        cuenta = CuentaPuntos(
            cliente_id=cliente.id,
            saldo_puntos=0,
            estado="activa",
        )
        db.add(cuenta)

        usuario = Usuario(
            correo=correo,
            celular=celular,
            password_hash=hash_password(payload.password),
            rol="cliente",
            activo=True,
            cliente_id=cliente.id,
        )
        db.add(usuario)

        db.commit()
        db.refresh(usuario)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=_build_duplicate_detail(),
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo completar el registro")

    try:
        session_token, _ = create_session_for_user(db, usuario, request)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="La cuenta fue creada, pero no se pudo iniciar la sesion automaticamente. Inicia sesion manualmente.",
        )
    _set_session_cookie(response, session_token)

    return TokenResponse(
        access_token=session_token,
        user=UsuarioOut.model_validate(usuario),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identificador = normalize_identifier(payload.identificador)
    rate_limit_key = _build_login_rate_limit_key(identificador, request)
    _ensure_login_not_blocked(rate_limit_key)

    usuario = (
        db.query(Usuario)
        .filter(
            or_(
                Usuario.correo == identificador,
                Usuario.celular == identificador,
            )
        )
        .first()
    )

    if not usuario:
        _register_failed_login_attempt(rate_limit_key)
        raise HTTPException(status_code=401, detail=_build_login_failure_detail())

    if not usuario.activo:
        _register_failed_login_attempt(rate_limit_key)
        raise HTTPException(status_code=401, detail=_build_login_failure_detail())

    if not verify_password(payload.password, usuario.password_hash):
        _register_failed_login_attempt(rate_limit_key)
        raise HTTPException(status_code=401, detail=_build_login_failure_detail())

    _clear_failed_login_attempts(rate_limit_key)

    try:
        session_token, _ = create_session_for_user(db, usuario, request)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo iniciar la sesion por un conflicto de sesiones. Intenta nuevamente.",
        )
    _set_session_cookie(response, session_token)

    return TokenResponse(
        access_token=session_token,
        user=UsuarioOut.model_validate(usuario),
    )


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def token_login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    payload = LoginRequest(
        identificador=form_data.username,
        password=form_data.password,
    )
    return login(payload, request, response, db)


@router.post("/logout")
def logout(
    response: Response,
    current_session: Sesion = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    revoke_session(db, current_session)
    db.commit()
    _clear_session_cookie(response)
    return {"detail": "Sesion cerrada correctamente"}


@router.get("/me", response_model=UsuarioOut)
def me(current_user: Usuario = Depends(get_current_user)):
    return UsuarioOut.model_validate(current_user)
