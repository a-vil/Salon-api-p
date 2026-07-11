class TestRewardsAdmin:
    def test_create_reward(self, client, admin_token):
        response = client.post(
            "/recompensas",
            json={
                "nombre": "Corte gratis",
                "descripcion": "Corte de cabello gratuito",
                "puntos_requeridos": 100,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Corte gratis"
        assert data["puntos_requeridos"] == 100
        assert data["activo"] is True
        assert "id" in data

    def test_create_reward_as_cliente_forbidden(self, client, cliente_token):
        response = client.post(
            "/recompensas",
            json={
                "nombre": "Corte gratis",
                "descripcion": "Corte de cabello gratuito",
                "puntos_requeridos": 100,
            },
            headers={"Authorization": f"Bearer {cliente_token}"},
        )
        assert response.status_code == 403

    def test_list_rewards_empty(self, client, admin_token):
        response = client.get(
            "/recompensas",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_rewards_with_data(self, client, admin_token):
        client.post(
            "/recompensas",
            json={"nombre": "Reward 1", "puntos_requeridos": 50},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        client.post(
            "/recompensas",
            json={"nombre": "Reward 2", "puntos_requeridos": 100},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response = client.get(
            "/recompensas",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_cliente_sees_only_active_rewards(self, client, admin_token, cliente_token):
        resp1 = client.post(
            "/recompensas",
            json={"nombre": "Activa", "puntos_requeridos": 50},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp1.status_code == 200, resp1.text
        create_resp = client.post(
            "/recompensas",
            json={"nombre": "Inactiva", "puntos_requeridos": 100},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_resp.status_code == 200, create_resp.text
        reward_id = create_resp.json()["id"]
        deact_resp = client.patch(
            f"/recompensas/{reward_id}/desactivar",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert deact_resp.status_code == 200, deact_resp.text
        response = client.get(
            "/recompensas",
            headers={"Authorization": f"Bearer {cliente_token}"},
        )
        assert response.status_code == 200
        names = [r["nombre"] for r in response.json()]
        assert "Activa" in names
        assert "Inactiva" not in names


class TestRewardsClient:
    def test_cliente_list_rewards(self, client, cliente_token):
        response = client.get(
            "/recompensas",
            headers={"Authorization": f"Bearer {cliente_token}"},
        )
        assert response.status_code == 200
