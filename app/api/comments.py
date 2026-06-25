from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import CommentCreateRequest, CommentResponse

router = APIRouter(prefix="/comments", tags=["comments"])


def to_comment_response(comment: Comment, user: User) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        user_email=user.email,
        target_type=comment.target_type,
        target_id=comment.target_id,
        content=comment.content,
        language=comment.language,
        created_at=comment.created_at,
    )


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    target_type: str,
    target_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    stmt = (
        select(Comment, User)
        .join(User, User.id == Comment.user_id)
        .where(
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.status == "visible",
        )
        .order_by(Comment.created_at.desc())
        .limit(100)
    )
    rows = (await session.execute(stmt)).all()
    return [to_comment_response(comment, user) for comment, user in rows]


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    payload: CommentCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment cannot be empty")

    comment = Comment(
        user_id=current_user.id,
        target_type=payload.target_type.strip().lower(),
        target_id=payload.target_id.strip().upper(),
        content=content,
        language=payload.language,
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return to_comment_response(comment, current_user)
