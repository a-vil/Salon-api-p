from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nombre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    apellido: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dni: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    celular: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    correo: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    fecha_naci: Mapped[date | None] = mapped_column(Date, nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_desactivacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    cuenta_puntos = relationship(
        "CuentaPuntos",
        back_populates="cliente",
        uselist=False,
        cascade="all, delete-orphan",
    )

    usuario = relationship(
        "Usuario",
        back_populates="cliente",
        uselist=False,
        cascade="all, delete-orphan",
    )

