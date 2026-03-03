from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from src.core.config import logger, settings
from src.core.retrieval import init_store
from src.endpoints import chart, chat, health

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    # Startup
    logger.info("Starting up...")
    # Docker layout: /app/main.py + /app/data/   → parent / "data"
    # Local layout:  api/main.py  + data/         → parent.parent / "data"
    _here = Path(__file__).resolve().parent
    data_dir = _here / "data" if (_here / "data").is_dir() else _here.parent / "data"
    count = init_store(str(data_dir))
    logger.info(f"Knowledge store ready: {count} documents")
    yield
    # Shutdown
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """
    Application Factory to create FastAPI instance.
    """

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Midway Config
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,  # ty:ignore[invalid-argument-type]
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include Routers (registered BEFORE static mount → API routes take priority)
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])

    app.include_router(
        chart.router, prefix=f"{settings.API_V1_STR}/chart", tags=["Chart"]
    )
    # ── Static file serving (production: built UI lives in ./static/) ────
    if STATIC_DIR.is_dir():
        logger.info(f"Serving static UI from: {STATIC_DIR}")

        # SPA catch-all: serve index.html for any non-API, non-file route
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            file_path = STATIC_DIR / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(STATIC_DIR / "index.html")
    else:
        logger.info("No static directory found — running in API-only mode")

    return app


app = create_app()


def main() -> None:
    """
    Entry point for running the application via script.
    """
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1,
    )


if __name__ == "__main__":
    main()
