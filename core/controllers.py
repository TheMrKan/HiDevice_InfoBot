from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.models import Controller


async def get_controller_async(db: AsyncSession, mqtt_user: str) -> Controller | None:
    sql = select(Controller).where(Controller.mqtt_user == mqtt_user).limit(1)
    result = await db.execute(sql)
    return result.scalar_one_or_none()


def check_auth(controller: Controller, mqtt_password: str) -> bool:
    return controller.mqtt_password == mqtt_password
