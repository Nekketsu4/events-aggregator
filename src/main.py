from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.v1.endpoints.events import router as event_router
from src.schemas.event_schemas import HealthResponse
from src.service.event_provider_client import provider_client
from src.worker.tasks import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan контекст: запускает и останавливает планировщик фоновых задач."""
    try:
        scheduler.start()
    except Exception:
        logger.exception("Не удалось запустить планировщик")
    try:
        yield
    finally:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            logger.exception("Ошибка при остановке планировщика")
            await provider_client.close()
        finally:
            await provider_client.close()


app = FastAPI(
    title="Events Aggregator",
    description="Бэкенд-сервис агрегатор для управления событиями и мероприятиями",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


app.include_router(event_router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")
