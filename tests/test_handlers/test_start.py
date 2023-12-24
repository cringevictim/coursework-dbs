from unittest.mock import AsyncMock

import pytest
from aiogram.utils.markdown import hbold
from aiogram_unittest import types

from main import command_start_handler

@pytest.mark.asyncio
async def test_starting_handler():
    message = AsyncMock()
    await command_start_handler(message)

    kb = [types.KeyboardButton(text="Поділитися номером☎️", request_contact=True)]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    message.anwer.assert_called_with(
        f"Вітаю, {hbold(message.from_user.full_name)}!\n"
        f"Для того, щоб продовжити роботу треба увійти у систему."
        f"\n\nБудь ласка, поділіться номером для входу:", reply_markup=keyboard)