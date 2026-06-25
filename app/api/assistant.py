from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.subscription import authorize_analysis
from app.services.trading_assistant import answer_trading_question

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantQuestion(BaseModel):
    question: str = Field(..., min_length=3, max_length=600)
    timeframe: str | None = None
    limit: int = 120


@router.post("/ask")
async def ask_trading_assistant(
    payload: AssistantQuestion,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    usage = await authorize_analysis(
        session=session,
        user=current_user,
        symbol="TRADING_ASSISTANT",
        timeframe=payload.timeframe or "auto",
    )
    result = await answer_trading_question(
        question=payload.question,
        timeframe=payload.timeframe,
        limit=payload.limit,
    )
    result["subscription"] = usage
    return result
