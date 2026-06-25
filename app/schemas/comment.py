from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    target_type: str = Field(min_length=2, max_length=30)
    target_id: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=2, max_length=2000)
    language: str = Field(default="fa", pattern="^(fa|en)$")


class CommentResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    target_type: str
    target_id: str
    content: str
    language: str
    created_at: datetime
