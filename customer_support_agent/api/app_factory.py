from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from customer_support_agent.api.routers import (
    drafts_router,
    knowledge_router,
    health_router,
    memory_router,
    tickets_router,
)

from customer_support_agent.core.settings import Settings,ensure_directories,get_settings
from customer_support_agent.repositories.sqlite import init_db



def create_app(settings: Settings | None = None) -> FastAPI:
    resolve_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        ensure_directories(resolve_settings)
        init_db()
        yield
    app = FastAPI(title=resolve_settings.app_name,lifespan=lifespan)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        """Send browser visits to the dashboard instead of returning an API 404."""
        return RedirectResponse(url="http://localhost:8501", status_code=307)

    app.include_router(health_router)
    app.include_router(knowledge_router)
    app.include_router(tickets_router)
    app.include_router(memory_router)
    app.include_router(drafts_router) 


    return app
        
