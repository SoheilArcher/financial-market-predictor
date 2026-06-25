from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.api.chart import router as chart_router
from app.api.comments import router as comments_router
from app.api.crypto_payments import router as crypto_payments_router
from app.api.iran_market import router as iran_market_router
from app.api.managed_portfolio import router as managed_portfolio_router
from app.api.market import router as market_router
from app.api.news import router as news_router
from app.api.analysis import router as analysis_router
from app.api.performance import router as performance_router
from app.api.report import router as report_router
from app.api.revenue import router as revenue_router
from app.api.social import router as social_router
from app.api.subscription import router as subscription_router
from app.api.symbols import router as symbols_router
from app.api.trade import router as trade_router

app = FastAPI(
    title="NexTrade",
    version="0.1",
)

web_dir = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=web_dir), name="static")

app.include_router(auth_router)
app.include_router(subscription_router)
app.include_router(admin_router)
app.include_router(assistant_router)
app.include_router(market_router)
app.include_router(analysis_router)
app.include_router(report_router)
app.include_router(chart_router)
app.include_router(comments_router)
app.include_router(crypto_payments_router)
app.include_router(iran_market_router)
app.include_router(managed_portfolio_router)
app.include_router(performance_router)
app.include_router(news_router)
app.include_router(social_router)
app.include_router(revenue_router)
app.include_router(symbols_router)
app.include_router(trade_router)


@app.get("/")
async def landing():
    return FileResponse(web_dir / "landing.html")


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return FileResponse(web_dir / "robots.txt", media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    return FileResponse(web_dir / "sitemap.xml", media_type="application/xml")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "project": "NexTrade",
        "dashboard": "/app",
    }


@app.get("/app", include_in_schema=False)
async def dashboard():
    return FileResponse(web_dir / "index.html")
