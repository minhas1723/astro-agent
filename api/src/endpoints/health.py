from fastapi import APIRouter
from pydantic import BaseModel
from src.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """
    Health check response model.
    """

    status: str
    version: str
    project: str


@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Check the health of the application.
    """
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        project=settings.PROJECT_NAME,
    )
