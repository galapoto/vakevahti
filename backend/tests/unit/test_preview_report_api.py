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


def test_preview_report_supports_audited_coordinator_decisions() -> None:
    client = _client()
    calls = client.get("/api/funding-calls").json()["items"]
    created = client.post(
        "/api/reports",
        json={"funding_call_ids": [calls[0]["id"]]},
    )
    report_id = created.json()["id"]
    client.post(f"/api/reports/{report_id}/submit")

    approved = client.post(
        f"/api/reports/{report_id}/decision",
        json={"decision": "APPROVE"},
    )

    assert approved.status_code == 200
    payload = approved.json()
    assert payload["status"] == "APPROVED"
    assert payload["approval_events"][0]["decision"] == "APPROVE"
    assert payload["approval_events"][0]["actor_source"] == "PREVIEW_FIXTURE"
    assert len(payload["approval_events"][0]["content_hash"]) == 64

    assert client.patch(
        f"/api/reports/{report_id}", json={"notes": "no mutation"}
    ).status_code == 409



def test_preview_report_rejects_client_supplied_approver_identity() -> None:
    client = _client()
    calls = client.get("/api/funding-calls").json()["items"]
    created = client.post(
        "/api/reports",
        json={"funding_call_ids": [calls[0]["id"]]},
    )
    report_id = created.json()["id"]
    client.post(f"/api/reports/{report_id}/submit")

    response = client.post(
        f"/api/reports/{report_id}/decision",
        json={"decision": "APPROVE", "actor_id": "spoofed-user"},
    )

    assert response.status_code == 422


def test_preview_report_queue_filters_waiting_approval() -> None:
    client = _client()
    calls = client.get("/api/funding-calls").json()["items"]
    created = client.post(
        "/api/reports",
        json={"funding_call_ids": [calls[0]["id"]]},
    )
    report_id = created.json()["id"]
    client.post(f"/api/reports/{report_id}/submit")

    queue = client.get("/api/reports", params={"status": "WAITING_APPROVAL"})
    assert queue.status_code == 200
    assert queue.json()["total"] >= 1
    assert report_id in {item["id"] for item in queue.json()["items"]}


def test_preview_approved_report_revision_preserves_original_version() -> None:
    client = _client()
    calls = client.get("/api/funding-calls").json()["items"]
    created = client.post(
        "/api/reports",
        json={"funding_call_ids": [calls[0]["id"]]},
    )
    report_id = created.json()["id"]
    client.post(f"/api/reports/{report_id}/submit")
    approved = client.post(
        f"/api/reports/{report_id}/decision",
        json={"decision": "APPROVE"},
    )
    assert approved.json()["version_number"] == 1

    revised = client.post(f"/api/reports/{report_id}/revise")
    assert revised.status_code == 200
    successor = revised.json()
    assert successor["status"] == "DRAFT"
    assert successor["version_number"] == 2
    assert successor["supersedes_report_id"] == report_id
    assert successor["approval_events"] == []

    repeated = client.post(f"/api/reports/{report_id}/revise")
    assert repeated.json()["id"] == successor["id"]
    original = client.get(f"/api/reports/{report_id}").json()
    assert original["status"] == "APPROVED"
    assert len(original["approval_events"]) == 1
