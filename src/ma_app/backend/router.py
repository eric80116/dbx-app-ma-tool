"""API router aggregation.

Every route module calls the singleton ``create_router()`` (the /api-prefixed router),
so importing them here registers all their routes. ``app.py`` includes this router plus
the bare ``/health`` router.
"""

from databricks.sdk.service.iam import User as UserOut

from .core import Dependencies, create_router
from .models import VersionOut

# Import route modules for their side effect: registering routes on the singleton.
from .routes import audiences as audiences  # noqa: F401
from .routes import campaigns as campaigns  # noqa: F401
from .routes import dashboard as dashboard  # noqa: F401
from .routes import health as health  # noqa: F401

router = create_router()


@router.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@router.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me(user_ws: Dependencies.UserClient):
    return user_ws.current_user.me()
