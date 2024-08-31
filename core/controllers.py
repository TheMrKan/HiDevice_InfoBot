from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.models import Controller, UserToController


async def get_controller_async(db: AsyncSession, mqtt_user: str) -> Controller | None:
    sql = select(Controller).where(Controller.mqtt_user == mqtt_user).limit(1)
    result = await db.execute(sql)
    return result.scalar_one_or_none()


async def get_controller_users_async(db: AsyncSession, controller: Controller) -> list[int]:
    sql = select(UserToController.user_id).where(UserToController.controller_user == controller.mqtt_user)
    result = await db.execute(sql)
    return list(result.scalars())


def check_auth(controller: Controller, mqtt_password: str) -> bool:
    return controller.mqtt_password == mqtt_password
