from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from core.models import User, Controller
from core import controllers


async def get_user_async(db: AsyncSession, tg_id: int) -> User | None:
    sql = select(User).options(joinedload(User.controllers)).where(User.id == tg_id).limit(1)
    result = await db.execute(sql)
    return result.unique().scalar_one_or_none()


async def create_user_async(db: AsyncSession, tg_id: int) -> User:
    user = User(tg_id)
    db.add(user)
    return user


class AuthorizationError(Exception):
    pass


async def authorize_controller_async(db: AsyncSession, user: User, mqtt_user: str, mqtt_password: str) -> bool:
    if any(c.mqtt_user == mqtt_user for c in user.controllers):
        return False

    controller = await controllers.get_controller_async(db, mqtt_user)
    if not controller or not controllers.check_auth(controller, mqtt_password):
        raise AuthorizationError()

    user.controllers.append(controller)
    return True

