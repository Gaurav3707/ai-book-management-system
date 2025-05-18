from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.services.userServices import UserService
from app.utils.decorators import token_required
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/register")
async def register(request: Request, user: UserService.UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Register endpoint called for user: {user.username}")
    return await UserService.register_user(user, db)

@router.post("/login")
async def login(request: Request, user: UserService.UserLogin, db: AsyncSession = Depends(get_db)):
    logger.info(f"Login endpoint called for user: {user.username}")
    return await UserService.login_user(user, db)

@router.get("/profile")
@token_required
async def get_profile(request: Request, user: dict = None):
    logger.info(f"Profile endpoint accessed for user: {user['sub']}")
    return await UserService.get_user_profile(user)
