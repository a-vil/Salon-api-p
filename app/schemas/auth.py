import re
from datetime import date

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.user import UsuarioOut


class LoginRequest(BaseModel):
    identificador: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioOut


class RegisterRequest(BaseModel):
    nombre: str
    apellido: str
    fecha_naci: date
    password: str
    correo: EmailStr | None = None
    celular: str | None = None
    dni: str | None = None

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, value: str | None):
        if value is None:
            return value
        value = re.sub(r"\D", "", value)
        if not value.isdigit() or len(value) != 9:
            raise ValueError("El celular debe tener exactamente 9 digitos")
        return value

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, value: str | None):
        if value is None:
            return value
        if not value.isdigit() or len(value) != 8:
            raise ValueError("El DNI debe tener exactamente 8 digitos")
        return value

    @field_validator("password")
    @classmethod
    def validar_password(cls, value: str):
        if len(value) < 8:
            raise ValueError("La contrasena debe tener al menos 8 caracteres")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contrasena no puede superar 72 bytes")
        return value

    @field_validator("apellido")
    @classmethod
    def validar_apellido(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("El apellido es obligatorio")
        return value

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("El nombre es obligatorio")
        return value

    @field_validator("correo")
    @classmethod
    def normalizar_correo(cls, value: EmailStr | None):
        if value is None:
            return value
        return value.lower()
