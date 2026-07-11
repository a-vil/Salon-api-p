from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Canje(Base):
    __tablename__ = "canjes"
    __table_args__ = (
        Index(
            "uq_canjes_cuenta_pendiente",
            "cuenta_id",
            unique=True,
            sqlite_where=text("estado = 'pendiente'"),
            postgresql_where=text("estado = 'pendiente'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cuenta_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas_puntos.id", ondelete="CASCADE"),
        nullable=False,
    )
    recompensa_id: Mapped[int] = mapped_column(ForeignKey("recompensas.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    puntos_usados: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_canje: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente", nullable=False)

    cuenta = relationship("CuentaPuntos", back_populates="canjes")
    recompensa = relationship("Recompensa", back_populates="canjes")
