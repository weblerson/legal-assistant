import asyncio
import logging
import os
import sys

import httpx

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    BotCommand,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["BOT_TOKEN"]

dp = Dispatcher()


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
            elif response.status_code == 204:
                await message.answer("Sessão inexistente. Nada a fazer.")

        except httpx.ConnectError:
            await message.answer(
                "Não consegui me conectar ao servidor para limpar a sessão.",
            )


@dp.message(Command("rate"))
async def show_rate(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ruim 😠",
                    callback_data="rate_bad",
                ),
                InlineKeyboardButton(
                    text="Boa 😐",
                    callback_data="rate_good",
                ),
                InlineKeyboardButton(
                    text="Excelente 🤩",
                    callback_data="rate_excellent",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Fechar ❌",
                    callback_data="close_menu",
                )
            ]
        ]
    )

    await message.answer("Avalie sua experiência!", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("rate_"))
async def process_rating(callback: CallbackQuery):
    rating_key = callback.data.split("_")[1]
    rating_map = {
        "bad": "Ruim",
        "good": "Bom",
        "excellent": "Excelente",
    }

    rating_value = rating_map.get(rating_key, 0)

    request_user_id = callback.from_user.id

    server_host = os.environ["SERVER_HOST"]
    server_url = f"{server_host}/rate/"

    payload = {
        "request_user_id": request_user_id,
        "rating": rating_key,
    }
    async with httpx.AsyncClient() as client:
        try:
            await callback.answer("Salvando...")

            response = await client.post(
                server_url,
                json=payload,
                timeout=10.0,
            )

            if response.status_code == 200:
                await callback.message.edit_text(
                    f"Obrigado! Nota <b>{rating_value}</b> registrada.",
                    reply_markup=None,
                )

            else:
                print(f"Server Error: {response.text}")
                await callback.message.edit_text(
                    "Erro ao salvar avaliação no servidor.",
                )

        except httpx.RequestError as e:
            print(f"Connection Error: {e}")
            await callback.message.edit_text(
                "Erro de conexão ao salvar avaliação.",
            )


@dp.callback_query(F.data == "close_menu")
async def close_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()


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

        await message.answer(response_json["response"])


async def main_async() -> None:
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

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )

    asyncio.run(main_async())
