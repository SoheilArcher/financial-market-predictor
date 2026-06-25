from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.market import router as market_router
from app.api.analysis import router as analysis_router
from app.api.subscription import router as subscription_router

app = FastAPI(
    title="Market AI Platform",
    version="0.1",
)

app.include_router(auth_router)
app.include_router(subscription_router)
app.include_router(admin_router)
app.include_router(market_router)
app.include_router(analysis_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "project": "Market AI Platform",
    }

