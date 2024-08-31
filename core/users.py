from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core.models import User, Controller, UserToController
from core import controllers


async def get_user_async(db: AsyncSession, tg_id: int) -> User | None:
    sql = select(User).where(User.id == tg_id).limit(1)
    result = await db.execute(sql)
    return result.scalar_one_or_none()


async def create_user_async(db: AsyncSession, tg_id: int) -> User:
    user = User(id=tg_id)
    db.add(user)
    return user


async def get_user_controllers_async(db: AsyncSession, user: User) -> list[str]:
    sql = select(UserToController.controller_user).where(UserToController.user_id == user.id)
    result = await db.execute(sql)
    return list(result.scalars())


class AuthorizationError(Exception):
    pass


async def authorize_controller_async(db: AsyncSession, user: User, mqtt_user: str, mqtt_password: str) -> bool:
    if mqtt_user in await get_user_controllers_async(db, user):
        return False

    controller = await controllers.get_controller_async(db, mqtt_user)
    if not controller or not controllers.check_auth(controller, mqtt_password):
        raise AuthorizationError()

    db.add(UserToController(user_id=user.id, controller_user=mqtt_user))
    return True


async def unauthorize_controller_async(db: AsyncSession, user: User, mqtt_user: str) -> bool:
    sql = delete(UserToController).where((UserToController.user_id == user.id) & (UserToController.controller_user == mqtt_user))
    result = await db.execute(sql)
    return result.rowcount > 0
