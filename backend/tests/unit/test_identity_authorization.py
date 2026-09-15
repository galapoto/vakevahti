from __future__ import annotations

import hmac
from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from app.security.identity import (
    ActorContext,
    FundingPermission,
    SignedGatewayIdentityProvider,
    gateway_signature_message,
    require_permission,
)

_TEST_SECRET = b"test-only-gateway-secret-32-bytes!!"
ApproveActor = Annotated[
    ActorContext,
    Depends(require_permission(FundingPermission.APPLICATIONS_APPROVE)),
]


def _gateway_app() -> FastAPI:
    app = FastAPI()
    app.state.identity_provider = SignedGatewayIdentityProvider(
        secret=_TEST_SECRET,
        max_age_seconds=300,
    )

    @app.get("/approve")
    async def approve(actor: ApproveActor) -> dict[str, str]:
        return {"actor_id": actor.actor_id, "source": actor.source}

    return app


def _headers(
    *,
    permissions: tuple[str, ...],
    issued_at: int | None = None,
    path: str = "/approve",
    query: str = "",
) -> dict[str, str]:
    actor_id = "coordinator-123"
    display_name = "Test Coordinator"
    permission_text = ",".join(sorted(permissions))
    issued_text = str(issued_at or int(datetime.now(UTC).timestamp()))
    signature = hmac.new(
        _TEST_SECRET,
        gateway_signature_message(
            actor_id=actor_id,
            display_name=display_name,
            permissions=permission_text,
            issued_at=issued_text,
            method="GET",
            path=path,
            query=query,
        ),
        sha256,
    ).hexdigest()
    return {
        "X-Vake-Actor-Id": actor_id,
        "X-Vake-Actor-Name": display_name,
        "X-Vake-Permissions": permission_text,
        "X-Vake-Identity-Issued-At": issued_text,
        "X-Vake-Identity-Signature": signature,
    }


def test_signed_gateway_identity_authorizes_explicit_permission() -> None:
    client = TestClient(_gateway_app())
    response = client.get(
        "/approve",
        headers=_headers(permissions=(FundingPermission.APPLICATIONS_APPROVE.value,)),
    )

    assert response.status_code == 200
    assert response.json() == {
        "actor_id": "coordinator-123",
        "source": "VAKETOMATTI_GATEWAY",
    }


def test_signed_gateway_identity_denies_missing_permission() -> None:
    client = TestClient(_gateway_app())
    response = client.get(
        "/approve",
        headers=_headers(permissions=(FundingPermission.OPPORTUNITIES_READ.value,)),
    )

    assert response.status_code == 403
    assert "funding.applications.approve" in response.json()["detail"]


def test_signed_gateway_identity_rejects_expired_or_request_replayed_signature() -> None:
    client = TestClient(_gateway_app())
    expired = int(datetime.now(UTC).timestamp()) - 600
    assert client.get(
        "/approve",
        headers=_headers(
            permissions=(FundingPermission.APPLICATIONS_APPROVE.value,),
            issued_at=expired,
        ),
    ).status_code == 401

    wrong_path_headers = _headers(
        permissions=(FundingPermission.APPLICATIONS_APPROVE.value,),
        path="/different-endpoint",
    )
    assert client.get("/approve", headers=wrong_path_headers).status_code == 401


def test_production_requires_signed_gateway_identity_configuration() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", identity_mode="development")

    with pytest.raises(ValidationError):
        Settings(identity_mode="gateway", identity_gateway_shared_secret="too-short")

    settings = Settings(
        app_env="production",
        identity_mode="gateway",
        identity_gateway_shared_secret="x" * 32,
    )
    assert settings.identity_mode == "gateway"


def test_preview_session_exposes_fixed_non_secret_identity_context() -> None:
    app = create_app(Settings(dashboard_preview_mode=True, enabled_sources="STM"))
    response = TestClient(app).get("/api/session")

    assert response.status_code == 200
    payload = response.json()
    assert payload["actor_id"] == "preview-coordinator"
    assert payload["identity_source"] == "PREVIEW_FIXTURE"
    assert FundingPermission.APPLICATIONS_APPROVE.value in payload["permissions"]
