import asyncio
import logging
import os
import sys

import httpx

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, MenuButton, BotCommand

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["BOT_TOKEN"]

dp = Dispatcher()

option_1 = KeyboardButton(text="Tope")
option_2 = KeyboardButton(text="+500 aura")

clear_session_button = KeyboardButton(text="/clear")

reply_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    input_field_placeholder="Limpar chat",
    keyboard=[[clear_session_button]],
)


# TODO: add feedback buttons
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """

    start_message = (
        "Olá! Sou o Assistente Legal!\n\n"
        "Sinta-se livre para tirar qualquer dúvida sobre "
        "o Código Civil, Código de Defesa do Consumidor "
        "e Código da Consolidação das Leis do Trabalho!"
    )

    await message.answer(start_message.strip())


@dp.message(Command("clear"))
async def command_clear_handler(message: Message) -> None:
    """
    This handler receives messages `/clear` command
    """
    server_host = os.environ["SERVER_HOST"]
    server_url = f"{server_host}/clear/"

    httpx_headers = httpx.Headers(
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    httpx_timeout = httpx.Timeout(timeout=200.0, connect=5.0)
    async with httpx.AsyncClient(
        headers=httpx_headers,
        timeout=httpx_timeout,
    ) as httpx_async_client:
        request_user_user_id = message.chat.id

        params = {
            "user_id": request_user_user_id,
        }

        try:
            response: httpx.Response = await httpx_async_client.delete(
                server_url,
                params=params,
            )
            if response.status_code == 200:
                await message.answer(
                    "Sessão limpa! 🧹\nPodemos começar de novo.",
                )
            else:
                # Tell the user it failed
                await message.answer(
                    "Ocorreu um erro ao tentar limpar a sessão no servidor.",
                )

        except httpx.ConnectError:
            await message.answer(
                "Não consegui me conectar ao servidor para limpar a sessão.",
            )


# TODO: implement session destruction handler
@dp.message()
async def question_handler(message: Message) -> None:
    """
    Handler will receive the user question and make a HTTP
    request to the server where the agent is hosted in
    and send back to the client the response.
    """

    server_host = os.environ["SERVER_HOST"]
    server_url = f"{server_host}/query/"

    httpx_headers = httpx.Headers(
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    httpx_timeout = httpx.Timeout(timeout=200.0, connect=5.0)
    async with httpx.AsyncClient(
        headers=httpx_headers,
        timeout=httpx_timeout,
    ) as httpx_async_client:
        request_user_username = (
            message.chat.first_name or message.chat.username
        )
        request_user_user_id = message.chat.id

        data = {
            "query": message.text,
            "username": request_user_username,
            "user_id": request_user_user_id,
        }

        response: httpx.Response = await httpx_async_client.post(
            server_url,
            json=data
        )
        response_json = response.json()
        print(response_json, end="\n\n\n")

        await message.answer(response_json["response"])


async def main_async() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    commands = [
        BotCommand(
            command="clear",
            description="Limpar chat"
        ),
        BotCommand(
            command="rate",
            description="Avaliar",
        )
    ]

    await bot.set_my_commands(commands)

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )

    asyncio.run(main_async())
