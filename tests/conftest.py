import os

os.environ["SECRET_KEY"] = "test_secret_key_12345678901234567890"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["SESSION_COOKIE_SAMESITE"] = "lax"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.core.security import hash_password
from app.models.user import Usuario
from app.models.client import Cliente
from app.models.points_account import CuentaPuntos
from app.models.points_movement import MovimientoPuntos
from app.models.reward import Recompensa

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_token(client, db_session):
    admin = Usuario(
        correo="admin@test.com",
        password_hash=hash_password("Admin123!"),
        rol="admin",
        activo=True,
    )
    db_session.add(admin)
    db_session.commit()

    response = client.post("/auth/login", json={
        "identificador": "admin@test.com",
        "password": "Admin123!",
    })
    client.cookies.clear()
    return response.json()["access_token"]


@pytest.fixture
def cliente_token(client, db_session):
    cliente = Cliente(nombre="Test", apellido="User", dni="12345678", activo=True)
    db_session.add(cliente)
    db_session.flush()

    cuenta = CuentaPuntos(cliente_id=cliente.id, saldo_puntos=0, estado="activa")
    db_session.add(cuenta)

    user = Usuario(
        correo="cliente@test.com",
        password_hash=hash_password("Cliente123!"),
        rol="cliente",
        activo=True,
        cliente_id=cliente.id,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/auth/login", json={
        "identificador": "cliente@test.com",
        "password": "Cliente123!",
    })
    client.cookies.clear()
    return response.json()["access_token"]
