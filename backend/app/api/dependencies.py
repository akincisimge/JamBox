import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.user import User
from app.services.rooms import get_user

DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    session: DatabaseSession,
    x_user_id: Annotated[uuid.UUID, Header(description="Current JamBox user ID")],
) -> User:
    return await get_user(session, x_user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]
