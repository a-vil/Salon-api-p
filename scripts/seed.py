from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import or_

from app.core.security import hash_password
from app.db import SessionLocal
from app.models.client import Cliente
from app.models.points_account import CuentaPuntos
from app.models.points_movement import MovimientoPuntos
from app.models.redeem import Canje
from app.models.reward import Recompensa
from app.models.user import Usuario


def main():
    db = SessionLocal()
    try:
        existing = db.query(Usuario).filter(
            or_(Usuario.correo == "admin@example.com", Usuario.correo == "cliente@example.com")
        ).first()
        if existing:
            print("Ya existen datos de ejemplo. Ejecuta 'alembic downgrade base && alembic upgrade head' para reiniciar.")
            return

        admin = Usuario(
            correo="admin@example.com",
            celular=None,
            password_hash=hash_password("Admin123!"),
            rol="admin",
            activo=True,
            cliente_id=None,
        )
        db.add(admin)

        cliente = Cliente(
            nombre="Maria",
            apellido="Garcia",
            dni="12345678",
            celular="987654321",
            correo="cliente@example.com",
            activo=True,
        )
        db.add(cliente)
        db.flush()

        cuenta = CuentaPuntos(
            cliente_id=cliente.id,
            saldo_puntos=150,
            estado="activa",
        )
        db.add(cuenta)

        cliente_usuario = Usuario(
            correo="cliente@example.com",
            celular="987654321",
            password_hash=hash_password("Cliente123!"),
            rol="cliente",
            activo=True,
            cliente_id=cliente.id,
        )
        db.add(cliente_usuario)

        mov1 = MovimientoPuntos(
            cuenta_id=cuenta.id,
            tipo="acumulacion",
            puntos=100,
            monto_compra=50.00,
            descripcion="Compra de corte y peinado",
        )
        db.add(mov1)

        mov2 = MovimientoPuntos(
            cuenta_id=cuenta.id,
            tipo="acumulacion",
            puntos=50,
            monto_compra=25.00,
            descripcion="Compra de tratamiento capilar",
        )
        db.add(mov2)

        recompensa1 = Recompensa(
            nombre="Corte de cabello gratis",
            descripcion="Un corte de cabello totalmente gratuito",
            puntos_requeridos=100,
            activo=True,
        )
        db.add(recompensa1)

        recompensa2 = Recompensa(
            nombre="30% de descuento en coloracion",
            descripcion="Descuento especial en cualquier servicio de coloracion",
            puntos_requeridos=200,
            activo=True,
        )
        db.add(recompensa2)

        recompensa3 = Recompensa(
            nombre="Manicure premium",
            descripcion="Manicure completo con esmaltado semipermanente",
            puntos_requeridos=80,
            activo=True,
        )
        db.add(recompensa3)

        db.commit()
        print("Datos de ejemplo creados exitosamente")
        print("  Admin:     admin@example.com / Admin123!")
        print("  Cliente:   cliente@example.com / Cliente123!")
        print("  Recompensas: 3 creadas")
        print("  Puntos del cliente: 150")
    finally:
        db.close()


if __name__ == "__main__":
    main()
