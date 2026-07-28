from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate


async def upsert_user(session: AsyncSession, payload: UserCreate) -> User:
    user = await session.scalar(select(User).where(User.spotify_id == payload.spotify_id))

    if user is None:
        user = User(**payload.model_dump())
        session.add(user)
    else:
        user.display_name = payload.display_name
        user.email = payload.email
        user.avatar_url = payload.avatar_url

    await session.commit()
    await session.refresh(user)
    return user
