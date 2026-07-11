from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CuentaPuntos(Base):
    __tablename__ = "cuentas_puntos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    saldo_puntos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="activa", nullable=False)
    fecha_afiliacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cliente = relationship("Cliente", back_populates="cuenta_puntos")
    movimientos = relationship(
        "MovimientoPuntos",
        back_populates="cuenta",
        cascade="all, delete-orphan",
    )
    canjes = relationship(
        "Canje",
        back_populates="cuenta",
        cascade="all, delete-orphan",
    )
