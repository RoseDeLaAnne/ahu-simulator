from fastapi.testclient import TestClient

from app.main import create_app


def test_dashboard_mount_serves_concept03_entrypoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200
    assert "theme-concept03" in response.text


def test_dashboard_entrypoint_contains_concept03_theme_bootstrap() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/dashboard?theme=concept03")

    assert response.status_code == 200
    assert "applyConcept03Theme" in response.text
    assert "theme-concept03" in response.text


def test_dashboard_entrypoint_contains_defense_variant_bootstrap() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/dashboard?theme=concept03&defense=true")

    assert response.status_code == 200
    assert "defenseActive" in response.text
    assert "c03-defense" in response.text


def test_concept03_dashboard_css_is_available() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/dashboard/assets/concept03_dashboard.css")

    assert response.status_code == 200
    assert "body.theme-concept03 #concept03-shell" in response.text


def test_concept03_mobile_css_is_available() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/dashboard/assets/concept03_mobile.css")

    assert response.status_code == 200
    assert "#mobile-bottom-nav" in response.text
    assert "c03-mobile-offcanvas--open" in response.text
