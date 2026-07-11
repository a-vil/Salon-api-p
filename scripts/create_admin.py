from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import or_

from app.core.security import hash_password, normalize_identifier
from app.db import SessionLocal
from app.models.client import Cliente
from app.models.points_account import CuentaPuntos
from app.models.points_movement import MovimientoPuntos
from app.models.redeem import Canje
from app.models.reward import Recompensa
from app.models.user import Usuario

email_adapter = TypeAdapter(EmailStr)


def main():
    correo_input = input("Correo del admin: ").strip().lower()
    correo = str(email_adapter.validate_python(correo_input))

    celular_input = input("Celular del admin (opcional): ").strip()
    celular = normalize_identifier(celular_input) if celular_input else None

    password = input("Contrasena del admin: ").strip()

    if len(password) < 8:
        raise ValueError("La contrasena debe tener al menos 8 caracteres")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contrasena no puede superar 72 bytes")

    db = SessionLocal()
    try:
        filters = [Usuario.correo == correo]
        if celular:
            filters.append(Usuario.celular == celular)

        existing = db.query(Usuario).filter(or_(*filters)).first()
        if existing:
            raise ValueError("Ya existe un usuario con ese correo o celular")

        admin = Usuario(
            correo=correo,
            celular=celular,
            password_hash=hash_password(password),
            rol="admin",
            activo=True,
            cliente_id=None,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Admin creado con ID {admin.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
