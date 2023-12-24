import asyncio
import logging
import sys
import subprocess
import json

from PostgreSQL import PostgreSQLDatabase
from Redis import RedisClient
from CouchDB import CouchDBClient

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters.callback_data import CallbackData
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.markdown import hbold


usersDB = PostgreSQLDatabase(db_name='users', db_user='postgres',
                             db_password='postgres')  # IGNORE WARNING
sessionDB = RedisClient()
flightsDB = CouchDBClient()
couchID: str

TOKEN = "6629800772:AAEeqrsuFFs61bm36Brc7mA8SlP7UKu_5qU"
router = Router()
dp = Dispatcher()
dp.include_router(router=router)


class Form(StatesGroup):
    login = State()
    registration = State()
    registed = State()
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

    kb = [types.KeyboardButton(text="Відмінити❌")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    number_check = usersDB.execute_read_query(
        "SELECT EXISTS (SELECT 1 FROM users WHERE phone = '" + message.contact.phone_number + "')")
    if number_check[0][0]:
        # sessionDB.set(message.from_user.id, message.contact.phone_number)
        sessionDB.set_hash(message.from_user.id, 'phone', message.contact.phone_number)
        await message.answer(reply_markup=keyboard, text="Введіть пароль:")
        await state.set_state(Form.login)
    else:
        # sessionDB.set(message.from_user.id, message.contact.phone_number)
        sessionDB.set_hash(message.from_user.id, 'phone', message.contact.phone_number)
        usersDB.execute_query("INSERT INTO users (phone) VALUES ('" + message.contact.phone_number + "')")
        kb1 = [types.KeyboardButton(text="Повернутися назад◀️")]
        keyboard1 = types.ReplyKeyboardMarkup(
            keyboard=[kb1],
            resize_keyboard=True)
        await message.answer(reply_markup=keyboard1, text="Цей номер не зареєстрований❌")
        await message.answer(reply_markup=keyboard1, text="Для реєстрації, придумайте пароль:")
        await state.set_state(Form.registration)


@router.message(Form.registration)
async def registration_handler(message: Message, state: FSMContext):
    print(message.text)
    usersDB.execute_query(
        "UPDATE users SET password = '" + message.text + "' WHERE phone = '" + sessionDB.get_hash(message.from_user.id,
                                                                                                  'phone') + "'")
    await state.clear()
    kb1 = [types.KeyboardButton(text="Продовжити▶️")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1],
        resize_keyboard=True)
    await message.answer(reply_markup=keyboard1, text=f"Пароль {message.text} збережений")


@router.message(F.text == "Продовжити▶️")
async def continue_handler(message: Message):
    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1],
        resize_keyboard=True)
    await message.answer(reply_markup=keyboard1, text="✅Реєстрація виконана!")


@router.message(Form.login)
async def login_handler(message: Message, state: FSMContext) -> None:
    print(message.text)
    password_check = usersDB.execute_read_query(
        "SELECT EXISTS (SELECT 1 FROM users WHERE password = '" + message.text + "' AND phone = '" + sessionDB.get_hash(
            message.from_user.id,
            'phone') + "')")
    admin_check = usersDB.execute_read_query(
        "SELECT EXISTS (SELECT 1 FROM users WHERE is_admin = 't' AND phone = '" + sessionDB.get_hash(
            message.from_user.id, 'phone') + "')")

    if password_check[0][0]:
        if admin_check[0][0]:
            kb1 = [types.KeyboardButton(text="Шукати квитки за номером користувача🔍")]
            keyboard1 = types.ReplyKeyboardMarkup(
                keyboard=[kb1],
                resize_keyboard=True)
            await message.answer("✅Вхід виконаний", reply_markup=keyboard1)
            await state.clear()
        else:
            kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
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
        await state.clear()
        await message.answer("Пароль неправильний❌")
        await message.answer("Введіть пароль ще раз:", reply_markup=keyboard)
        await state.set_state(Form.login)


@router.message(F.text == "Шукати квитки🔍")
async def search_for_tickets_handler(message: Message, state: FSMContext) -> None:
    kb = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)
    await state.set_state(Form.dest1)
    await message.answer("Введіть пункт відправлення:", reply_markup=keyboard)


@router.message(Form.dest1)
async def dep_point_handler(message: Message, state: FSMContext) -> None:
    kb = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)
    await state.set_state(Form.dest2)
    await message.answer("Введіть пункт призначення:", reply_markup=keyboard)

    sessionDB.set_hash(message.from_user.id, 'data', message.text)


def find_flights(departure, arrival, json_data):
    matching_flights = []
    data = json.dumps(json_data, indent=4)
    for flight in data['flights']:
        if flight["departure"] == departure and flight["arrival"] == arrival:
            matching_flights.append(flight)

    return matching_flights

@router.message(Form.dest2)
async def search_handler(message: Message, state: FSMContext) -> None:
    await message.answer("🔍Шукаємо квитки...")
    departure = sessionDB.get_hash(message.from_user.id, 'data')
    result = [flight for flight in flightsDB.get_document('flights', couchID)['flights'] if flight['departure'] == departure and flight['arrival'] == message.text]
    sessionDB.set_hash(message.from_user.id, 'data1', message.text)
    if result != []:
        kb = [types.KeyboardButton(text="Обрати квиток✈️"), types.KeyboardButton(text="Шукати квитки🔍")]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[kb],
            resize_keyboard=True)


        await message.answer(f"Доступні квитки:")
        for i in range(0, len(result)):
            result_to_print = str(
                str(result[i]['departure']) + " -> " + str(
                    result[i]['arrival']) + " || " + str(
                    result[i]['departure_time']) + " -> " + str(result[i]['arrival_time']))
            await message.answer(f"{i+1}) {result_to_print}", reply_markup=keyboard)
    else:
        kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
        keyboard1 = types.ReplyKeyboardMarkup(
            keyboard=[kb1],
            resize_keyboard=True)
        await message.answer("Квитків по вашому запиту не знайдено.", reply_markup=keyboard1)
    await state.clear()


@router.message(F.text == "Обрати квиток✈️")
async def search_for_tickets_handler(message: Message, state: FSMContext) -> None:
    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1],
        resize_keyboard=True)
    await message.answer("Вкажіть номер позиції щоб обрати квиток:", reply_markup=keyboard1)
    await state.set_state(Form.select)


@router.message(Form.select)
async def select_tickets_handler(message: Message, state: FSMContext) -> None:
    global message_to_int
    kb = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    tickets = [flight for flight in flightsDB.get_document('flights', couchID)['flights'] if flight['departure'] == sessionDB.get_hash(message.from_user.id, 'data') and flight['arrival'] == sessionDB.get_hash(message.from_user.id, 'data1')]

    try:
        message_to_int = int(message.text)
        if message_to_int not in range(1,len(tickets)+1):
            await message.answer(f"❌Виберіть квиток, ввівши число від 1 до {len(tickets)}", reply_markup=keyboard)
        else:
            selected_ticket = tickets[int(message.text)-1]
            print(selected_ticket)

            #query_string_1 = str("Місце відправлення: " + str(selected_ticket['departure'])+ "\nМісце прибуття: "+ str(selected_ticket['arrival']) +"\nЧас відправлення: "+ str(selected_ticket['departure_time']) +"\nЧас прибуття: "+ str(selected_ticket['arrival_time']))
            query_string_1 = str(
                str(selected_ticket['departure']) + " -> " + str(
                    selected_ticket['arrival']) + " || " + str(
                    selected_ticket['departure_time']) + " -> " + str(selected_ticket['arrival_time']))
            print(query_string_1)
            query_string_2 = str(sessionDB.get_hash(message.from_user.id, 'phone'))
            print(query_string_2)
            usersDB.execute_query("UPDATE users SET tickets = '"+query_string_1+"' WHERE phone = '" + query_string_2 + "'")

            await message.answer(f"Ваш квиток: \n{str(query_string_1)}", reply_markup=keyboard)
            await state.clear()

    except Exception as e:
        print(e)
        await message.answer(f"❌Сталася помилка", reply_markup=keyboard)



@router.message(F.text == "Мій квиток🎫")
async def search_for_user_tickets_handler(message: Message) -> None:
    query_string_2 = str(sessionDB.get_hash(message.from_user.id, 'phone'))
    tickets_str = manipulate_string(str(usersDB.execute_read_query("SELECT tickets FROM users WHERE phone = '"+query_string_2+"'")))

    kb = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)
    if tickets_str != "":
        await message.answer(f"🎫Заброньований квиток:\n{tickets_str}", reply_markup=keyboard)
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

    search_result =  manipulate_string(usersDB.execute_read_query("SELECT tickets FROM users WHERE phone = '"+message.text+"'"))

    if search_result == "":
        search_result = "❌Нема даних"
    await message.answer(f"Пошук виконано:\n{search_result}", reply_markup=keyboard)


def manipulate_string(input_string):
    if len(input_string) >= 7:
        modified_string = input_string[3:-4]
        return modified_string
    else:
        return "String is too short"

async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    subprocess.run("docker compose up -d", shell=True)

    usersDB.connect()
    flightsDB.create_database(db_name='flights')

    couchID = flightsDB.push_example_data(db_name='flights')

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


