from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class MovimientoPuntos(Base):
    __tablename__ = "movimientos_puntos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cuenta_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas_puntos.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    puntos: Mapped[int] = mapped_column(Integer, nullable=False)
    monto_compra: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha_movimiento: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cuenta = relationship("CuentaPuntos", back_populates="movimientos")
