from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.endpoints.events import router as event_router
from src.schemas.event_schemas import HealthResponse
from src.worker.tasks import scheduler

# Добавить логирование


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan контекст для управления состоянием приложения"""
    scheduler.start()
    yield
    scheduler.shutdown()
    # Завершаем работу


app = FastAPI(
    title="Events Aggregator",
    description="Бэкенд-сервис агрегатор для управления событиями и мероприятиями",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(event_router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")
