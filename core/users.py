from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, exists
import logging

from core.models import User, Controller, UserToController
from core import controllers


logger = logging.getLogger(__name__)


async def get_user_async(db: AsyncSession, tg_id: int) -> User | None:
    sql = select(User).where(User.id == tg_id).limit(1)
    result = await db.execute(sql)
    return result.scalar_one_or_none()


async def create_user_async(db: AsyncSession, tg_id: int) -> User:
    user = User(id=tg_id)
    db.add(user)
    logger.info("Created user %s", tg_id)
    return user


async def get_user_controllers_async(db: AsyncSession, user: User) -> list[str]:
    sql = select(UserToController.controller_user).where(UserToController.user_id == user.id)
    result = await db.execute(sql)
    return list(result.scalars())


async def has_controller_async(db: AsyncSession, user: User, mqtt_user: str) -> bool:
    sql = exists().where((UserToController.user_id == user.id) & (UserToController.controller_user == mqtt_user)).select()
    return (await db.execute(sql)).scalar()


class AuthorizationError(Exception):
    pass


async def authorize_controller_async(db: AsyncSession, user: User, mqtt_user: str, mqtt_password: str) -> bool:
    if await has_controller_async(db, user, mqtt_user):
        logger.debug("Failed to add controller %s to user %s: already authorized", mqtt_user, user.id)
        return False

    controller = await controllers.get_controller_async(db, mqtt_user)
    if not controller or not controllers.check_auth(controller, mqtt_password):
        raise AuthorizationError()

    db.add(UserToController(user_id=user.id, controller_user=mqtt_user))
    logger.info("Added controller %s to user %s", mqtt_user, user.id)
    return True


async def unauthorize_controller_async(db: AsyncSession, user: User, mqtt_user: str) -> bool:
    sql = delete(UserToController).where((UserToController.user_id == user.id) & (UserToController.controller_user == mqtt_user))
    result = await db.execute(sql)
    if result.rowcount > 0:
        logger.info("Removed controller %s from user %s", mqtt_user, user.id)
        return True
    else:
        logger.debug("Failed to remove controller %s from user %s: not authorized", mqtt_user, user.id)
        return False
