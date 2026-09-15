from typing import Annotated

from fastapi import APIRouter, Depends

from app.security.identity import ActorContext, get_actor_context

router = APIRouter(prefix="/api", tags=["identity"])
ActorDependency = Annotated[ActorContext, Depends(get_actor_context)]


@router.get("/session")
async def session_identity(actor: ActorDependency) -> dict[str, object]:
    """Expose the current authenticated actor without exposing tokens or secrets."""

    return {
        "actor_id": actor.actor_id,
        "display_name": actor.display_name,
        "identity_source": actor.source,
        "permissions": sorted(permission.value for permission in actor.permissions),
    }
