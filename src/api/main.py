"""LiquidityFlow FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from src.api.routes_etl import router as etl_router
from src.api.routes_portfolio import router as portfolio_router
from src.api.routes_quality import router as quality_router
from src.db import get_engine, initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database(get_engine())
    yield


app = FastAPI(
    title="LiquidityFlow ETL API",
    version="1.0.0",
    description="Investment management ETL, data quality, liquidity, and rate stress services.",
    lifespan=lifespan,
)
app.include_router(etl_router)
app.include_router(portfolio_router)
app.include_router(quality_router)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "liquidityflow-etl", "version": app.version}
