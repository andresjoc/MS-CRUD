import pytest
from fastapi.testclient import TestClient
from main import app
from dependencies.auth_guard import get_current_user_from_token, TokenUser

client = TestClient(app)

def test_crud_health_check():
    """Verifica que el servicio esté arriba y responda el health check"""
    response = client.get("/")
    assert response.status_code == 200
    assert "HeartSense MSCRUD is running" in response.json().get("message", "")

def test_protected_route_rejects_unauthorized():
    """Verifica que rutas protegidas rechacen peticiones sin token (401)"""
    response = client.get("/App_users/1")
    assert response.status_code == 401

def test_protected_route_with_mocked_user():
    """Verifica que el guardián permita el acceso con usuario autenticado"""
    # Mock de autenticación simulando el usuario autenticado
    app.dependency_overrides[get_current_user_from_token] = lambda: TokenUser(user_id=1, email="test@heartsense.com")
    try:
        response = client.get("/compute_statuses/")
        assert response.status_code in (200, 500)
    finally:
        app.dependency_overrides.clear()
