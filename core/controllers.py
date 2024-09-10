from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from core.models import Controller, UserToController
import mqtt


NOTIFICATIONS = [
    "channel_status",
    "dry_mode",
    "clock_error"
]


logger = logging.getLogger(__name__)


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


def get_controller_notifications(controller: Controller) -> dict[str, bool]:
    return {
        key: __is_notifications_enabled(controller.notifications, i) for i, key in enumerate(NOTIFICATIONS)
    }


def __is_notifications_enabled(notifications_int: int, index: int):
    return bool(notifications_int & (1 << index))


async def switch_notifications_async(controller: Controller, notifications_key: str) -> bool:
    index = NOTIFICATIONS.index(notifications_key)
    was_enabled = __is_notifications_enabled(controller.notifications, index)
    logger.info("[%s] %s - %s", controller.mqtt_user, notifications_key.upper(),
                "ENABLED" if not was_enabled else "DISABLED")

    if was_enabled:
        controller.notifications = __disable_notifications(controller.notifications, index)
    else:
        controller.notifications = __enable_notifications(controller.notifications, index)

    await mqtt.send_async(controller.mqtt_user, f"${controller.notifications}")

    return not was_enabled


def __enable_notifications(notifications_int: int, index: int) -> int:
    return notifications_int | (1 << index)


def __disable_notifications(notifications_int: int, index: int) -> int:
    return notifications_int & ~(1 << index)
