import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters.callback_data import CallbackData
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.markdown import hbold

#                          !!!WARNING!!!
#                  DO NOT CREATE GLOBAL VARIABLES
#                  ONLY FUNCTION-RANGE VARIABLES
#                    THAT'S WHY SESSION DB EXISTS


TOKEN = "6629800772:AAEeqrsuFFs61bm36Brc7mA8SlP7UKu_5qU"
router = Router()
dp = Dispatcher()
dp.include_router(router=router)


class Form(StatesGroup):
    login = State()
    success = State()
    dest1 = State()
    dest2 = State()
    select = State()
    selected = State()
    not_selected = State()
    admin_search = State()


class LoginSuccess(CallbackData, prefix="login_success"):
    num: int


class LoginCallback(CallbackData, prefix="login"):
    phone: str
    id: str
    num: int


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    kb = [types.KeyboardButton(text="Поділитися номером☎️", request_contact=True)]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)
    await message.answer(
        f"Вітаю, {hbold(message.from_user.full_name)}!\n"
        f"Для того, щоб продовжити роботу треба увійти у систему."
        f"\n\nБудь ласка, поділіться номером для входу:", reply_markup=keyboard)


@router.message((F.text == "Відмінити❌") | (F.text == "Повернутися назад◀️"))
async def enter_new_number_handler(message: Message, state=FSMContext) -> None:
    await state.clear()
    kb = [types.KeyboardButton(text="Поділитися номером☎️", request_contact=True)]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)
    await message.answer("Для входу в систему необхідно надати номер:", reply_markup=keyboard)


@router.message(F.contact)
async def share_phone_number_handler(message: Message, state: FSMContext) -> None:
    # message.contact.phone_number      # UNCOMMENT TO GET USER'S PHONE NUMBER
    # message.from_user.id              # UNCOMMENT TO GET USER'S TELEGRAM ID
    # TODO: user base - stores phone numbers, passwords and field admin [TRUE OR FALSE], not editable from
    #  the bot interface

    # TODO: session base - fields: user_id (message.from_user.id [can be called everywhere]), phone number
    #  (message.contact.phone_number [can be called only in this function]), departure prompt, arrival prompt.
    #  It's not possible to get user's phone number in any time without creating global variables
    #  (which are not allowed), so for matching current user and his login data with corresponding content of db's must
    #  be used user_id as bridge between phone number and user's prompt.
    #  I recommend to create get_phone(user_id: str) to build future requests easily.

    kb = [types.KeyboardButton(text="Відмінити❌")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    number_check = True  # TODO: if number exists (TRUE or FALSE)

    if number_check is True:
        await message.answer(reply_markup=keyboard, text="Введіть пароль:")
        await state.set_state(Form.login)
    else:
        kb1 = [types.KeyboardButton(text="Повернутися назад◀️")]
        keyboard1 = types.ReplyKeyboardMarkup(
            keyboard=[kb1],
            resize_keyboard=True)
        await message.answer(reply_markup=keyboard1, text="Цей номер не зареєстрований❌")


@router.message(Form.login)
async def login_handler(message: Message, state: FSMContext) -> None:
    password_check = True  # TODO: check password and check if user is admin
    admin_check = True

    if password_check:
        if admin_check:
            kb1 = [types.KeyboardButton(text="Шукати квитки за номером користувача🔍")]
            keyboard1 = types.ReplyKeyboardMarkup(
                keyboard=[kb1],
                resize_keyboard=True)
            await message.answer("✅Вхід виконаний", reply_markup=keyboard1)
            await state.clear()
        else:
            kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мої квитки🎫")]
            keyboard1 = types.ReplyKeyboardMarkup(
                keyboard=[kb1],
                resize_keyboard=True)
            await message.answer("✅Вхід виконаний", reply_markup=keyboard1)
            await state.clear()
    else:
        kb = [types.KeyboardButton(text="Відмінити❌")]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[kb],
            resize_keyboard=True)
        await message.answer("Пароль неправильний❌.")
        await message.answer("Введіть пароль ще раз:", reply_markup=keyboard)


@router.message(F.text == "Шукати квитки🔍")
async def search_for_tickets_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.dest1)
    await message.answer("Введіть пункт відправлення:")


@router.message(Form.dest1)
async def dep_point_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.dest2)
    await message.answer("Введіть пункт призначення:")

    # message.text            # departure prompt
    # message.from_user.id    # user's id
    # TODO: add DEP (departure) to session table (not arrival here, not a mistake)


@router.message(Form.dest2)
async def search_handler(message: Message, state: FSMContext) -> None:
    await message.answer("🔍Шукаємо квитки...")

    # message.text            # departure prompt
    # message.from_user.id    # user's id
    # TODO: add ARR (arrival) to session table

    # TODO: flights db request by dep, arr from session table with matching parameters
    result = "квитки"
    if result != None:
        kb = [types.KeyboardButton(text="Обрати квиток✈️"), types.KeyboardButton(text="Шукати квитки🔍")]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[kb],
            resize_keyboard=True)
        await message.answer(f"Доступні квитки: \n{result}", reply_markup=keyboard)
    else:
        kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мої квитки🎫")]
        keyboard1 = types.ReplyKeyboardMarkup(
            keyboard=[kb1],
            resize_keyboard=True)
        await message.answer("Квитків по вашому запиту не знайдено.", reply_markup=keyboard1)
    await state.clear()


@router.message(F.text == "Обрати квиток✈️")
async def search_for_tickets_handler(message: Message, state: FSMContext) -> None:
    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мої квитки🎫")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1],
        resize_keyboard=True)
    await message.answer("Вкажіть номер позиції щоб обрати квиток:", reply_markup=keyboard1)
    await state.set_state(Form.select)


@router.message(Form.select)
async def select_tickets_handler(message: Message, state: FSMContext) -> None:
    global message_to_int
    kb = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мої квитки🎫")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    available_tickets_amount = 5
    # TODO: get_available_tickets_amount() (independent but kinda similar to request from search_handler function)

    try:
        message_to_int = int(message.text)
        if message_to_int in range(1, available_tickets_amount + 1):
            # TODO: write selected by sequence number ticket into the user tickets db
            await message.answer(f"✅Білет {message.text} заброньований.", reply_markup=keyboard)
        else:
            await message.answer("❌Недопустиме значення!")
        await state.clear()
    except:
        await message.answer("❌Обрана позиція повинна бути числом.", reply_markup=keyboard)
        await state.clear()


@router.message(F.text == "Мої квитки🎫")
async def search_for_user_tickets_handler(message: Message) -> None:
    tickets_str = "квитки"
    # TODO: ask session db by user's id to get user's phone number,
    #  then ask tickets_db to get booked tickets by user's phone number. Set up simple parser to return a list which
    #  will be displayed to the user. Leave empty str if there are no matches.


    kb = [types.KeyboardButton(text="Обрати квиток✈️"), types.KeyboardButton(text="Шукати квитки🔍")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)
    if tickets_str != "":
        await message.answer(f"🎫Заброньовані квитки:\n{tickets_str}", reply_markup=keyboard)
    else:
        await message.answer(f"🎫У вас ще нема заброньованих квитків.", reply_markup=keyboard)

@router.message(F.text == "Шукати квитки за номером користувача🔍")
async def admin_search_for_user_tickets_handler(message: Message, state: FSMContext) -> None:
    await message.answer("Введіть повний номер телефону (+380...):")
    await state.set_state(Form.admin_search)

@router.message(Form.admin_search)
async def admin_search_handler(message: Message, state: FSMContext) -> None:
    await state.update_data()
    kb = [types.KeyboardButton(text="Шукати квитки за номером користувача🔍")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    search_result = ""

    # TODO: literally request from search_for_user_tickets_handler function, idk how to implement
    #  neo4j in here. Don't know don't care

    if search_result == "":
        search_result = "❌Нема даних"
    await message.answer(f"Пошук виконано:\n{search_result}", reply_markup=keyboard)



async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
