from uuid import uuid4

import redis


async def instantiate_redis_client(
        host: str,
        port: int,
        db: int = 0,
) -> redis.Redis:
    client = redis.Redis(host, port, db)

    return client


async def _generate_user_id(username: bytes) -> str:
    random_uuid = str(uuid4())
    user_id = f"{username}-{random_uuid}"

    return user_id


async def set_user_id(
        chat_user_id: str,
        username: str,
        client: redis.Redis,
) -> str:
    user_id = await _generate_user_id(username.encode())
    client.set(chat_user_id, user_id)

    return client.get(chat_user_id)


async def retrieve_user_id(
        chat_user_id: str,
        client: redis.Redis,
) -> str | None:
    user_id = client.get(chat_user_id)
    if user_id is not None:
        return user_id.decode()

    return user_id


async def pop_user_id(chat_user_id: str, client: redis.Redis) -> None:
    client.delete(chat_user_id)
