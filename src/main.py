from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan контекст для управления состоянием приложения"""
    # Пока что ничего не делает
    yield
    # Завершаем работу


app = FastAPI(
    title="Events Aggregator",
    description="Бэкенд-сервис агрегатор для управления событиями и мероприятиями",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health/")
async def health_check():
    return {"status": "ok"}
