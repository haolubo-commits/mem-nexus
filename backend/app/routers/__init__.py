from app.routers.health import router as health_router
from app.routers.episodes import router as episodes_router
from app.routers.entities import router as entities_router
from app.routers.relations import router as relations_router
from app.routers.graph import router as graph_router
from app.routers.recall import router as recall_router

__all__ = [
    "health_router",
    "episodes_router",
    "entities_router",
    "relations_router",
    "graph_router",
    "recall_router",
]
