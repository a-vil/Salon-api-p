from datetime import date


class TestRegister:
    def test_register_cliente_success(self, client):
        response = client.post("/auth/register", json={
            "nombre": "Juan",
            "apellido": "Perez",
            "fecha_naci": "1995-06-15",
            "password": "MiPassword123!",
            "correo": "juan@example.com",
            "celular": "999888777",
            "dni": "87654321",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["rol"] == "cliente"
        assert data["user"]["correo"] == "juan@example.com"

    def test_register_duplicate_email(self, client):
        client.post("/auth/register", json={
            "nombre": "Juan",
            "apellido": "Perez",
            "fecha_naci": "1995-06-15",
            "password": "MiPassword123!",
            "correo": "duplicate@example.com",
        })
        response = client.post("/auth/register", json={
            "nombre": "Otro",
            "apellido": "User",
            "fecha_naci": "1990-01-01",
            "password": "MiPassword123!",
            "correo": "duplicate@example.com",
        })
        assert response.status_code == 409

    def test_register_short_password(self, client):
        response = client.post("/auth/register", json={
            "nombre": "Juan",
            "apellido": "Perez",
            "fecha_naci": "1995-06-15",
            "password": "123",
            "correo": "juan2@example.com",
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_with_email(self, client):
        client.post("/auth/register", json={
            "nombre": "Ana",
            "apellido": "Lopez",
            "fecha_naci": "1990-01-01",
            "password": "AnaPassword1!",
            "correo": "ana@example.com",
        })
        response = client.post("/auth/login", json={
            "identificador": "ana@example.com",
            "password": "AnaPassword1!",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={
            "nombre": "Luis",
            "apellido": "Torres",
            "fecha_naci": "1988-03-20",
            "password": "LuisPass1!",
            "correo": "luis@example.com",
        })
        response = client.post("/auth/login", json={
            "identificador": "luis@example.com",
            "password": "WrongPassword1!",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", json={
            "identificador": "noexisto@example.com",
            "password": "SomePass1!",
        })
        assert response.status_code == 401


class TestMe:
    def test_me_authenticated(self, client):
        client.post("/auth/register", json={
            "nombre": "Carmen",
            "apellido": "Rivas",
            "fecha_naci": "1992-07-10",
            "password": "CarmenPass1!",
            "correo": "carmen@example.com",
        })
        login_resp = client.post("/auth/login", json={
            "identificador": "carmen@example.com",
            "password": "CarmenPass1!",
        })
        token = login_resp.json()["access_token"]
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["correo"] == "carmen@example.com"

    def test_me_unauthenticated(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401
