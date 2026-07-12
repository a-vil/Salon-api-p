# Mini Salon API

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-purple)
![JWT](https://img.shields.io/badge/Auth-JWT-black?logo=jsonwebtokens)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)
[![Tests](https://github.com/a-vil/Salon-api-p/actions/workflows/tests.yml/badge.svg)](https://github.com/a-vil/Salon-api-p/actions/workflows/tests.yml)

Backend del sistema de fidelidad para un salón de belleza. Los clientes se registran, acumulan puntos por consumos y los canjean por recompensas. Los administradores gestionan clientes, puntos, recompensas y canjes.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| Framework web | FastAPI |
| Servidor ASGI | Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Migraciones | Alembic |
| Base de datos | PostgreSQL (produccion) / SQLite (desarrollo) |
| Driver BD | psycopg2-binary |
| Validacion | Pydantic + Pydantic Settings |
| Autenticacion | JWT (PyJWT) + sesiones con hash SHA-256 |
| Contrasenas | Passlib + bcrypt |
| Documentacion | fastapi-swagger-dark |
| Despliegue | Render (web service + PostgreSQL) |

---

## Estructura del proyecto

```
app/
├── core/         # Configuracion, seguridad, dependencias
├── models/       # Modelos SQLAlchemy (Usuario, Cliente, CuentaPuntos, etc.)
├── routers/      # Endpoints por dominio (auth, clientes, puntos, recompensas, canjes)
├── schemas/      # Pydantic schemas para request/response
└── main.py       # Entry point de la API
alembic/          # Migraciones de base de datos
scripts/          # Utilidades (seed, crear admin)
tests/            # Tests automatizados (pytest)
```

---

## Caracteristicas destacadas

| Problema | Solucion implementada |
|---|---|
| Un cliente podria tener multiples sesiones activas | Revocacion automatica de sesiones anteriores al crear una nueva |
| Un canje pendiente bloquearia nuevos canjes | Validacion de 1 canje pendiente maximo por cliente (BD + aplicacion) |
| Desactivar cliente debe bloquear todo | Desactivacion en cascada: Usuario + CuentaPuntos |
| Seguridad en sesiones | Token SHA-256, expiracion configurable, renovacion con intervalo ("touch") |
| Trazabilidad de acciones admin | Log estructurado en JSON por cada operacion (AuditoriaAdmin) |
| Datos inconsistentes (correo, celular) | Normalizacion: correo a minusculas, celular solo digitos |
| Registro de cliente con multiples entidades | Transaccion unica: Cliente + CuentaPuntos + Usuario |

---

## Modelos de datos

| Modelo | Descripcion | Relaciones clave |
|---|---|---|
| `Usuario` | Autenticacion y roles (admin, cliente) | pertenece a `Cliente` via `cliente_id` |
| `Cliente` | Datos de negocio del cliente | tiene `CuentaPuntos` y `Usuario` |
| `CuentaPuntos` | Saldo de puntos del cliente | 1 a 1 con `Cliente` |
| `MovimientoPuntos` | Historial de transacciones (acumulacion, canje) | pertenece a `CuentaPuntos` |
| `Recompensa` | Catalogo de recompensas canjeables | activa/inactiva |
| `Canje` | Solicitud de canje (pendiente, confirmado, cancelado) | relaciona `Cliente` y `Recompensa` |
| `Sesion` | Sesiones activas con hash, IP y user-agent | pertenece a `Usuario` |
| `AuditoriaAdmin` | Log JSON de acciones de administradores | referencia `Usuario` admin |

---

## API endpoints

### Auth
| Metodo | Ruta | Descripcion |
|---|---|---|
| POST | `/auth/register` | Registro de cliente (crea Usuario + Cliente + CuentaPuntos) |
| POST | `/auth/login` | Login por correo o celular |
| GET | `/auth/me` | Perfil del usuario autenticado |

### Cliente (autoconsulta)
| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/clientes/mi-cuenta` | Datos del perfil propio |
| GET | `/puntos/mis-puntos` | Saldo de puntos propio |
| GET | `/puntos/mis-movimientos` | Historial de movimientos propio |
| GET | `/recompensas` | Catalogo de recompensas disponibles |
| GET | `/recompensas/{id}` | Detalle de una recompensa |
| POST | `/canjes` | Solicitar un canje |
| GET | `/canjes/mis-canjes` | Historial de canjes propios |

### Admin
| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/clientes` | Listar todos los clientes |
| GET | `/clientes/{id}` | Detalle de un cliente |
| PATCH | `/clientes/{id}` | Actualizar datos de un cliente |
| PATCH | `/clientes/{id}/desactivar` | Desactivar cliente (cascada) |
| PATCH | `/clientes/{id}/activar` | Reactivar cliente |
| GET | `/puntos/movimientos` | Todos los movimientos del sistema |
| GET | `/puntos/clientes/{id}` | Saldo de un cliente especifico |
| GET | `/puntos/clientes/{id}/movimientos` | Movimientos de un cliente especifico |
| POST | `/puntos/acumular` | Acumular puntos a un cliente |
| POST | `/recompensas` | Crear recompensa |
| GET | `/recompensas` | Listar recompensas |
| GET | `/recompensas/{id}` | Detalle de recompensa |
| PATCH | `/recompensas/{id}` | Actualizar recompensa |
| PATCH | `/recompensas/{id}/desactivar` | Desactivar recompensa |
| PATCH | `/recompensas/{id}/activar` | Activar recompensa |
| GET | `/canjes` | Listar todos los canjes |
| PATCH | `/canjes/{id}/confirmar` | Confirmar canje (admin) |
| PATCH | `/canjes/{id}/cancelar` | Cancelar canje (admin) |

---

## Instalacion y uso local

### Con Python (local)

```bash
# 1. Clonar el repositorio
git clone https://github.com/a-vil/Salon-api-p.git
cd Salon-api-p

# 2. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux / Mac
pip install -r requirements.txt

# 3. Copiar el archivo de entorno
cp .env.example .env

# 4. Ejecutar migraciones
alembic upgrade head

# 5. (Opcional) Cargar datos de ejemplo
python scripts/seed.py

# 6. Iniciar servidor
uvicorn app.main:app --reload
```

La API estara disponible en `http://localhost:8000`.  
Documentacion Swagger: `http://localhost:8000/docs`.

### Con Docker (requiere Docker Desktop)

```bash
docker compose up
```

Esto levanta la API + PostgreSQL automaticamente.  
La API estara disponible en `http://localhost:8000`.

---

## Variables de entorno

| Variable | Obligatoria | Default | Descripcion |
|---|---|---|---|
| `SECRET_KEY` | Si | — | Clave secreta para JWT (min. 32 caracteres) |
| `DATABASE_URL` | No | `sqlite:///./app.db` | URL de conexion a BD |
| `ALGORITHM` | No | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Tiempo de expiracion del token |
| `ENABLE_DOCS` | No | `true` | Habilita Swagger UI |
| `SESSION_EXPIRE_MINUTES` | No | `480` | Duracion de sesion (8 horas) |
| `SESSION_COOKIE_NAME` | No | `mini_salon_session` | Nombre de la cookie de sesion |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Origenes permitidos (separados por coma) |

---

## Datos de ejemplo

El script `scripts/seed.py` crea datos de prueba para explorar la API:

| Tipo | Credencial / Dato |
|---|---|
| Admin | `admin@example.com` / `Admin123!` |
| Cliente | `cliente@example.com` / `Cliente123!` |
| Recompensa 1 | Corte de cabello gratis — 100 puntos |
| Recompensa 2 | 30% descuento en coloracion — 200 puntos |
| Recompensa 3 | Manicure premium — 80 puntos |
| Cliente | 150 puntos acumulados, 2 movimientos |

Ejecutar: `python scripts/seed.py` (requiere migraciones aplicadas).

---

## Tests

16 tests automatizados que cubren autenticacion (registro, login, perfil),
recompensas (CRUD, permisos por rol) y health check.

```bash
python -m pytest tests/ -v
```

---

## Despliegue

El proyecto esta configurado para desplegarse en **Render**:

- **Web service**: Python, comando `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Base de datos**: PostgreSQL (plan free)
- **Frontend**: Repositorio separado (React). La URL del frontend se configura via `CORS_ORIGINS`.

Ver `render.yaml` para la configuracion completa.

---

## Roadmap

- Recuperacion de acceso (olvido de contrasena)
- Rate limiting
- Documentacion mejorada del flujo de canjes
- Mejoras de concurrencia

## Licencia

Este proyecto usa **PolyForm Noncommercial License 1.0.0**: puedes ver, probar,
modificar y aprender del código libremente, pero no se permite su uso con
fines comerciales. Ver [LICENSE](./LICENSE) para el texto completo.