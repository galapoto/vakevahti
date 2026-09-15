from __future__ import annotations

import hmac
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Protocol, cast

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings


class FundingPermission(StrEnum):
    OPPORTUNITIES_READ = "funding.opportunities.read"
    OPPORTUNITIES_REVIEW = "funding.opportunities.review"
    APPLICATIONS_EDIT = "funding.applications.edit"
    APPLICATIONS_APPROVE = "funding.applications.approve"
    ADMIN = "funding.admin"


ALL_FUNDING_PERMISSIONS = frozenset(FundingPermission)


@dataclass(frozen=True)
class ActorContext:
    actor_id: str
    display_name: str | None
    permissions: frozenset[FundingPermission]
    source: str

    def allows(self, permission: FundingPermission) -> bool:
        return FundingPermission.ADMIN in self.permissions or permission in self.permissions


class IdentityProvider(Protocol):
    async def authenticate(self, request: Request) -> ActorContext: ...


@dataclass(frozen=True)
class StaticIdentityProvider:
    actor: ActorContext

    async def authenticate(self, request: Request) -> ActorContext:
        del request
        return self.actor


@dataclass(frozen=True)
class SignedGatewayIdentityProvider:
    secret: bytes
    max_age_seconds: int

    async def authenticate(self, request: Request) -> ActorContext:
        actor_id = request.headers.get("x-vake-actor-id", "").strip()
        display_name = request.headers.get("x-vake-actor-name", "").strip() or None
        raw_permissions = request.headers.get("x-vake-permissions", "").strip()
        issued_at = request.headers.get("x-vake-identity-issued-at", "").strip()
        signature = request.headers.get("x-vake-identity-signature", "").strip().lower()
        if not actor_id or not issued_at or not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated organization identity is required.",
            )

        try:
            issued_epoch = int(issued_at)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid organization identity timestamp.",
            ) from exc

        now_epoch = int(datetime.now(UTC).timestamp())
        age = now_epoch - issued_epoch
        if age < -30 or age > self.max_age_seconds:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organization identity assertion is expired or not yet valid.",
            )

        canonical_permissions = _canonical_permissions(raw_permissions)
        expected = hmac.new(
            self.secret,
            gateway_signature_message(
                actor_id=actor_id,
                display_name=display_name,
                permissions=canonical_permissions,
                issued_at=issued_at,
                method=request.method,
                path=request.url.path,
                query=request.url.query,
            ),
            sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organization identity signature is invalid.",
            )

        parsed_permissions: set[FundingPermission] = set()
        for raw in canonical_permissions.split(",") if canonical_permissions else ():
            try:
                parsed_permissions.add(FundingPermission(raw))
            except ValueError:
                continue
        return ActorContext(
            actor_id=actor_id,
            display_name=display_name,
            permissions=frozenset(parsed_permissions),
            source="VAKETOMATTI_GATEWAY",
        )


def _canonical_permissions(raw_permissions: str) -> str:
    values = {value.strip() for value in raw_permissions.split(",") if value.strip()}
    return ",".join(sorted(values))


def gateway_signature_message(
    *,
    actor_id: str,
    display_name: str | None,
    permissions: str,
    issued_at: str,
    method: str,
    path: str,
    query: str,
) -> bytes:
    """Canonical request-bound message signed by the trusted identity gateway."""

    return "\n".join(
        [
            actor_id,
            display_name or "",
            permissions,
            issued_at,
            method.upper(),
            path,
            query,
        ]
    ).encode("utf-8")


def build_identity_provider(settings: Settings) -> IdentityProvider:
    if settings.dashboard_preview_mode:
        return StaticIdentityProvider(
            ActorContext(
                actor_id="preview-coordinator",
                display_name="Kehitysesikatselun koordinaattori",
                permissions=ALL_FUNDING_PERMISSIONS,
                source="PREVIEW_FIXTURE",
            )
        )
    if settings.identity_mode == "gateway":
        secret = settings.identity_gateway_shared_secret.get_secret_value().encode("utf-8")
        return SignedGatewayIdentityProvider(
            secret=secret,
            max_age_seconds=settings.identity_gateway_max_age_seconds,
        )
    return StaticIdentityProvider(
        ActorContext(
            actor_id="development-user",
            display_name="Development user",
            permissions=ALL_FUNDING_PERMISSIONS,
            source="DEVELOPMENT_STATIC",
        )
    )


def get_identity_provider(request: Request) -> IdentityProvider:
    return cast(IdentityProvider, request.app.state.identity_provider)


async def get_actor_context(request: Request) -> ActorContext:
    provider = get_identity_provider(request)
    return await provider.authenticate(request)


ActorDependency = Annotated[ActorContext, Depends(get_actor_context)]


def require_permission(
    permission: FundingPermission,
) -> Callable[[ActorContext], Awaitable[ActorContext]]:
    async def dependency(actor: ActorDependency) -> ActorContext:
        if not actor.allows(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}",
            )
        return actor

    return dependency
