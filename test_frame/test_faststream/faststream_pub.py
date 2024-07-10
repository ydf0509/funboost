

async def pub():
    async with TestKafkaBroker(broker) as br:
        await br.publish({
            "user": "John",
            "user_id": 1,
        }, "in")