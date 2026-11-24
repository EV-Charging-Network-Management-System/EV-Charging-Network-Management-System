"""Serve the built SPA alongside the API in the hosted demo."""

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            root = path.split("/", 1)[0]
            if exc.status_code != 404 or root in {"api", "ocpp", "assets"} or "." in path:
                raise
            return await super().get_response("index.html", scope)
