from fastapi.testclient import TestClient

from app.main import create_app


CONCEPT03_SCENARIOS = {
    "baseline_office_winter": "layout-grid",
    "summer_eco": "sun",
    "night_min_airflow": "moon",
    "freeze_protection": "refresh-cw",
    "airflow_check_100": "flame",
}


def test_concept03_scenarios_are_available_with_icons() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/scenarios")

    assert response.status_code == 200
    scenario_map = {item["id"]: item for item in response.json()}
    for scenario_id, icon in CONCEPT03_SCENARIOS.items():
        assert scenario_map[scenario_id]["icon"] == icon
        assert scenario_map[scenario_id]["source"] == "system"
        assert scenario_map[scenario_id]["locked"] is True


def test_concept03_test_scenario_runs_with_extended_control_mode() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/scenarios/airflow_check_100/run")

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "airflow_check_100"
    assert body["parameters"]["control_mode"] == "test"
