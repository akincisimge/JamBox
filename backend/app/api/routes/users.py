from fastapi import APIRouter, status

from app.api.dependencies import DatabaseSession
from app.schemas.user import UserCreate, UserResponse
from app.services.users import upsert_user

router = APIRouter(prefix="/users")


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_user(
    payload: UserCreate,
    session: DatabaseSession,
) -> UserResponse:
    user = await upsert_user(session, payload)
    return UserResponse.model_validate(user)
