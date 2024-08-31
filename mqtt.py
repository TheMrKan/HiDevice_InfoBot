import asyncio
import traceback
import asyncio_mqtt as aiomqtt

import config
import broadcaster


async def listen_async():
    async with aiomqtt.Client(config.MQTT_HOST, config.MQTT_PORT, username=config.MQTT_USER, password=config.MQTT_PASSWORD) as client:
        async with client.messages() as messages:
            await client.subscribe("+/telegram")
            async for message in messages:
                try:
                    await handle_message_async(str(message.topic), message.payload.decode("utf-8"))
                except:
                    traceback.print_exc()


def get_mqtt_user(topic: str) -> str:
    return topic.split("/")[0]


async def handle_message_async(topic: str, message: str):
    mqtt_user = get_mqtt_user(topic)
    await broadcaster.broadcast_async(mqtt_user, message)


if __name__ == "__main__":
    # https://pypi.org/project/asyncio-mqtt/#note-for-windows-users
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(listen_async())

