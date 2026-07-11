def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_method_not_allowed(client):
    response = client.post("/")
    assert response.status_code == 405
