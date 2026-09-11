from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(
                dashboard_preview_mode=True,
                enabled_sources="STM,HAEAVUSTUKSIA,EURA,SITRA,ACADEMY",
            )
        )
    )


def test_preview_report_can_be_saved_read_and_submitted() -> None:
    client = _client()

    created = client.post(
        "/api/reports",
        json={
            "title": "VakeHyvän rahoitusraportti",
            "notes": "Koordinaattorin testimuistiinpano",
            "funding_call_ids": [9001, 9006],
        },
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["status"] == "DRAFT"
    assert [item["funding_call_id"] for item in payload["items"]] == [9001, 9006]
    assert payload["items"][0]["snapshot"]["relevance_reason"]

    report_id = payload["id"]
    fetched = client.get(f"/api/reports/{report_id}")
    assert fetched.status_code == 200
    assert fetched.json()["notes"] == "Koordinaattorin testimuistiinpano"

    submitted = client.post(f"/api/reports/{report_id}/submit")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "WAITING_APPROVAL"
    assert submitted.json()["submitted_for_approval_at"] is not None

    repeated = client.post(f"/api/reports/{report_id}/submit")
    assert repeated.status_code == 200
    assert repeated.json()["submitted_for_approval_at"] == submitted.json()[
        "submitted_for_approval_at"
    ]


def test_preview_report_rejects_unknown_funding_calls() -> None:
    response = _client().post(
        "/api/reports",
        json={"funding_call_ids": [999999]},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {"missing_funding_call_ids": [999999]}
