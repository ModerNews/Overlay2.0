from .base_class import StreamOverlay

from .routers.websocket import websocket_router
from .routers.main import router

__all__ = ["create_app", "StreamOverlay"]


def create_app() -> StreamOverlay:
    """
    Initiates app and mounts routers to it. App shouldn't be initiated outside this function.
    """
    app = StreamOverlay()

    app.include_router(router)
    app.include_router(websocket_router)

    return app
