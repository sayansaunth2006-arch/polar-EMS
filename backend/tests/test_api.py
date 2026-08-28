"""API-level integration tests against a seeded in-memory SQLite DB."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_success(client: TestClient):
    r = client.post("/auth/login", json={"email": "operator@test.demo", "password": "operator123"})
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "operator"
    assert "access_token" in body


def test_login_wrong_password_is_rejected(client: TestClient):
    r = client.post("/auth/login", json={"email": "operator@test.demo", "password": "wrong-password"})
    assert r.status_code == 401


def test_protected_route_requires_auth(client: TestClient):
    r = client.get("/energy/current")
    assert r.status_code == 401


def test_me_endpoint_returns_current_user(client: TestClient, operator_token: str):
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "operator@test.demo"


def test_energy_current_has_expected_shape(client: TestClient, operator_token: str):
    r = client.get("/energy/current", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    body = r.json()
    for key in ("demand_kw", "solar_kw", "wind_kw", "battery_soc_pct", "renewable_contribution_pct", "is_synthetic"):
        assert key in body
    assert body["is_synthetic"] is True


def test_battery_status_reports_valid_soc_range(client: TestClient, operator_token: str):
    r = client.get("/battery/status", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    assert 0 <= r.json()["soc_pct"] <= 100


def test_generator_status_ok(client: TestClient, operator_token: str):
    r = client.get("/generator/status", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    assert r.json()["rated_capacity_kw"] > 0


def test_loads_listing_ok(client: TestClient, operator_token: str):
    r = client.get("/loads/", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_admin_can_change_load_priority(client: TestClient, admin_token: str):
    r = client.patch("/loads/1", headers={"Authorization": f"Bearer {admin_token}"}, json={"priority": 2})
    assert r.status_code == 200
    assert r.json()["priority"] == 2


def test_scientist_cannot_change_load_priority(client: TestClient, scientist_token: str):
    r = client.patch("/loads/1", headers={"Authorization": f"Bearer {scientist_token}"}, json={"priority": 2})
    assert r.status_code == 403


def test_optimization_recommendations_ok(client: TestClient, operator_token: str):
    r = client.get("/optimization/recommendations", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["recommendations"]) >= 1
    assert body["recommendations"][0]["kind"] == "ai_recommendation"


def test_simulation_scenarios_listed(client: TestClient, operator_token: str):
    r = client.get("/simulation/scenarios", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    keys = {s["key"] for s in r.json()}
    assert "solar_drop" in keys
    assert "generator_unavailable" in keys


def test_simulation_run_generator_unavailable_produces_result(client: TestClient, operator_token: str):
    r = client.post("/simulation/run/generator_unavailable", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["result"]["generator_output_kw"] == 0


def test_simulation_unknown_scenario_returns_404(client: TestClient, operator_token: str):
    r = client.post("/simulation/run/not-a-real-scenario", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 404


def test_what_if_battery_soc_zero_never_returns_negative_soc(client: TestClient, operator_token: str):
    r = client.post(
        "/simulation/what-if",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"battery_soc_override_pct": 0},
    )
    assert r.status_code == 200
    assert r.json()["result"]["battery_soc_pct"] >= 0


def test_anomaly_scan_and_list(client: TestClient, operator_token: str):
    h = {"Authorization": f"Bearer {operator_token}"}
    r = client.post("/anomaly/scan", headers=h)
    assert r.status_code == 200
    r = client.get("/anomaly/", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_alerts_generate_and_resolve(client: TestClient, operator_token: str):
    h = {"Authorization": f"Bearer {operator_token}"}
    client.post("/alerts/generate", headers=h)
    r = client.get("/alerts/", headers=h)
    assert r.status_code == 200
    alerts = r.json()
    if alerts:
        alert_id = alerts[0]["id"]
        r = client.post(f"/alerts/{alert_id}/resolve", headers=h)
        assert r.status_code == 200
        assert r.json()["is_resolved"] is True


def test_analytics_summary_24h(client: TestClient, operator_token: str):
    r = client.get("/analytics/summary?range=24h", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    assert "totals" in r.json()


def test_reports_generate(client: TestClient, operator_token: str):
    r = client.get("/reports/generate?range=7d", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["is_synthetic"] is True
    assert "estimated_savings_note" in body


def test_weather_current_ok(client: TestClient, operator_token: str):
    r = client.get("/weather/current", headers={"Authorization": f"Bearer {operator_token}"})
    assert r.status_code == 200
    assert r.json()["available"] is True
