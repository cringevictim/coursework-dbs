import asyncio
import logging
import sys
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

admin_password = '1111'

users_db = PostgreSQLDatabase(db_name='users', db_user='postgres', db_password='postgres')
user_cache = RedisClient()
flights_db = CouchDBClient()
couchID: str

TOKEN = "6465778947:AAFD4MTAqvFYByAjUjC1-WPaKk0GTej_d98"
router = Router()
dp = Dispatcher()
dp.include_router(router=router)


class Form(StatesGroup):
    login = State()
    registration = State()
    dest1 = State()
    dest2 = State()
    select = State()
    selected = State()
    admin_search = State()
    waiting_old_password = State()
    waiting_new_password = State()
    waiiting_admin_password = State()


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
    kb = [types.KeyboardButton(text="Відмінити❌")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    users_db_record_to_find = {
        'phone': message.contact.phone_number
    }

    number_check = users_db.contains_record(table_name='users', record=users_db_record_to_find)
    if number_check:
        user_cache.set_hash(message.from_user.id, key='phone', value=message.contact.phone_number)
        await message.answer(reply_markup=keyboard, text="Введіть пароль:")
        await state.set_state(Form.login)
    else:
        user_cache.set_hash(message.from_user.id, key='phone', value=message.contact.phone_number)
        users_db.insert_record(table_name='users', data=users_db_record_to_find)
        kb1 = [types.KeyboardButton(text="Повернутися назад◀️")]
        keyboard1 = types.ReplyKeyboardMarkup(
            keyboard=[kb1],
            resize_keyboard=True)
        await message.answer(reply_markup=keyboard1, text="Цей номер не зареєстрований❌")
        await message.answer(reply_markup=keyboard1, text="Для реєстрації, придумайте пароль:")
        await state.set_state(Form.registration)


@router.message(Form.registration)
async def registration_handler(message: Message, state: FSMContext):
    users_db_updated_record = {
        'password': message.text
    }
    users_db_where_clause = "phone = '" + user_cache.get_hash(message.from_user.id, key='phone') + "'"
    print(users_db_where_clause)
    users_db.update_record(table_name='users', data=users_db_updated_record, where_clause=users_db_where_clause)

    await state.clear()
    kb1 = [types.KeyboardButton(text="Продовжити▶️")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1],
        resize_keyboard=True)
    await message.answer(reply_markup=keyboard1, text="Пароль збережений")


@router.message(F.text == "Продовжити▶️")
async def continue_handler(message: Message):
    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    kb2 = [types.KeyboardButton(text="Налаштування⚙️"), types.KeyboardButton(text="Вихід❌")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1, kb2],
        resize_keyboard=True)
    await message.answer(reply_markup=keyboard1, text="✅Реєстрація виконана!")


@router.message(Form.login)
async def login_handler(message: Message, state: FSMContext) -> None:
    users_db_record_to_find = {
        'password': message.text,
        'phone': user_cache.get_hash(message.from_user.id, key='phone')
    }
    password_check = users_db.contains_record(table_name='users', record=users_db_record_to_find)

    users_db_record_to_find = {
        'is_admin': 't',
        'phone': user_cache.get_hash(message.from_user.id, key='phone')
    }
    admin_check = users_db.contains_record(table_name='users', record=users_db_record_to_find)

    if password_check:
        if admin_check:
            kb1 = [types.KeyboardButton(text="Шукати квитки за номером користувача🔍")]
            keyboard1 = types.ReplyKeyboardMarkup(
                keyboard=[kb1],
                resize_keyboard=True)
            await message.answer("✅Вхід виконаний", reply_markup=keyboard1)
            await state.clear()
        else:
            kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
            kb2 = [types.KeyboardButton(text="Налаштування⚙️")]
            keyboard1 = types.ReplyKeyboardMarkup(
                keyboard=[kb1, kb2],
                resize_keyboard=True)
            await message.answer("✅Вхід виконаний", reply_markup=keyboard1)
            await state.clear()
    else:
        kb = [types.KeyboardButton(text="Відмінити❌")]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[kb],
            resize_keyboard=True)
        await state.clear()
        await message.answer("Пароль неправильний!")
        await message.answer("Введіть пароль ще раз:", reply_markup=keyboard)
        await state.set_state(Form.login)


@router.message(F.text == "На головну🏠")
async def go_to_main_menu_handler(message: Message, state: FSMContext) -> None:
    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    kb2 = [types.KeyboardButton(text="Налаштування⚙️")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1, kb2],
        resize_keyboard=True)
    await message.answer("Оберіть опцію:", reply_markup=keyboard1)
    await state.clear()


@router.message(F.text == "Шукати квитки🔍")
async def search_for_tickets_handler(message: Message, state: FSMContext) -> None:
    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    kb2 = [types.KeyboardButton(text="На головну🏠")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb1, kb2],
        resize_keyboard=True)
    await state.set_state(Form.dest1)
    await message.answer("Введіть пункт відправлення:", reply_markup=keyboard)


@router.message(F.text == "Налаштування⚙️")
async def user_settings_handler(message : Message, state: FSMContext) -> None:
    kb1 = [types.KeyboardButton(text="Змінити пароль🔐"), types.KeyboardButton(text="Стати адміністратором👨‍💼")]
    kb2 = [types.KeyboardButton(text="На головну🏠")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb1, kb2],
        resize_keyboard=True)
    await message.answer(reply_markup=keyboard, text="Оберіть опцію:")


@router.message(F.text == "Змінити пароль🔐")
async def user_settings_handler(message : Message, state: FSMContext) -> None:
    await message.answer(text="Введіть старий пароль:")
    await state.set_state(Form.waiting_old_password)


@router.message(F.text == "Стати адміністратором👨‍💼")
async def user_admin_handler(message : Message, state: FSMContext) -> None:
    await message.answer(text="Введіть пароль адміністратора:")
    await state.set_state(Form.waiiting_admin_password)


@router.message(Form.waiting_old_password)
async def receive_old_password_handler(message: Message, state: FSMContext):
    users_db_password = {
        'phone': user_cache.get_hash(message.from_user.id, key='phone'),
        'password': message.text
    }
    password_is_correct = users_db.contains_record(table_name='users', record=users_db_password)

    if password_is_correct:
        await message.answer("Введіть новий пароль:")
        await state.set_state(Form.waiting_new_password)
    else:
        await message.answer("Введено неправильний старий пароль!")
        await state.set_state(Form.login)


@router.message(Form.waiting_new_password)
async def set_new_password_handler(message: Message, state: FSMContext):
    users_db_password = {
        'password': message.text
    }
    users_db.update_record(table_name='users', data=users_db_password, where_clause="phone = '" + user_cache.get_hash(message.from_user.id, key='phone') + "'")

    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    kb2 = [types.KeyboardButton(text="Налаштування⚙️")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1, kb2],
        resize_keyboard=True)
    await message.answer("✅Пароль успішно оновлено!", reply_markup=keyboard1)
    await state.clear()


@router.message(Form.waiiting_admin_password)
async def receive_old_password_handler(message: Message, state: FSMContext):
    if message.text == admin_password:
        users_db_admin = {
            'is_admin': 't'
        }
        users_db.update_record(table_name='users', data=users_db_admin, where_clause="phone = '" + user_cache.get_hash(message.from_user.id, key='phone') + "'")
        kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
        kb2 = [types.KeyboardButton(text="Налаштування⚙️")]
        keyboard1 = types.ReplyKeyboardMarkup(
            keyboard=[kb1, kb2],
            resize_keyboard=True)
        await message.answer("✅Ви стали адміністратором!", reply_markup=keyboard1)
        await state.clear()
    else:
        await message.answer("Введено неправильний пароль адміністратора!")
        await state.set_state(Form.login)


@router.message(Form.dest1)
async def dep_point_handler(message: Message, state: FSMContext) -> None:
    kb = [types.KeyboardButton(text="На головну🏠")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)
    await state.set_state(Form.dest2)
    await message.answer("Введіть пункт призначення:", reply_markup=keyboard)

    user_cache.set_hash(message.from_user.id, 'data', message.text)


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
    departure = user_cache.get_hash(message.from_user.id, key='data')
    result = [flight for flight in flights_db.get_document('flights', couchID)['flights'] if
              flight['departure'] == departure and flight['arrival'] == message.text]
    user_cache.set_hash(message.from_user.id, key='data1', value=message.text)
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
            await message.answer(f"{i + 1}) {result_to_print}", reply_markup=keyboard)
    else:
        kb1 = [types.KeyboardButton(text="На головну🏠")]
        keyboard1 = types.ReplyKeyboardMarkup(
            keyboard=[kb1],
            resize_keyboard=True)
        await message.answer("Квитків по вашому запиту не знайдено.", reply_markup=keyboard1)
    await state.clear()


@router.message(F.text == "Обрати квиток✈️")
async def search_for_tickets_handler(message: Message, state: FSMContext) -> None:
    kb1 = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    kb2 = [types.KeyboardButton(text="На головну🏠")]
    keyboard1 = types.ReplyKeyboardMarkup(
        keyboard=[kb1, kb2],
        resize_keyboard=True)
    await message.answer("Вкажіть номер позиції, щоб обрати квиток:", reply_markup=keyboard1)
    await state.set_state(Form.select)


@router.message(Form.select)
async def select_tickets_handler(message: Message, state: FSMContext) -> None:
    global message_to_int
    kb = [types.KeyboardButton(text="Шукати квитки🔍"), types.KeyboardButton(text="Мій квиток🎫")]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[kb],
        resize_keyboard=True)

    tickets = [flight for flight in flights_db.get_document('flights', couchID)['flights'] if
               flight['departure'] == user_cache.get_hash(message.from_user.id, key='data') and flight[
                   'arrival'] == user_cache.get_hash(message.from_user.id, key='data1')]

    try:
        message_to_int = int(message.text)
        if message_to_int not in range(1, len(tickets) + 1):
            await message.answer(f"❌Виберіть квиток, ввівши число від 1 до {len(tickets)}", reply_markup=keyboard)
        else:
            selected_ticket = tickets[int(message.text) - 1]
            print(selected_ticket)

            # query_string_1 = str("Місце відправлення: " + str(selected_ticket['departure'])+ "\nМісце прибуття: "+ str(selected_ticket['arrival']) +"\nЧас відправлення: "+ str(selected_ticket['departure_time']) +"\nЧас прибуття: "+ str(selected_ticket['arrival_time']))
            query_string_1 = str(
                str(selected_ticket['departure']) + " -> " + str(
                    selected_ticket['arrival']) + " || " + str(
                    selected_ticket['departure_time']) + " -> " + str(selected_ticket['arrival_time']))
            print(query_string_1)
            query_string_2 = str(user_cache.get_hash(message.from_user.id, 'phone'))
            print(query_string_2)
            users_db_updated_record = {
                'tickets': query_string_1
            }
            users_db.update_record(table_name='users', data=users_db_updated_record, where_clause="phone = '" + query_string_2 + "'")

            await message.answer(f"Ваш квиток: \n{str(query_string_1)}", reply_markup=keyboard)
            await state.clear()

    except Exception as e:
        print(e)
        await message.answer(f"❌Сталася помилка", reply_markup=keyboard)


@router.message(F.text == "Мій квиток🎫")
async def search_for_user_tickets_handler(message: Message) -> None:
    query_string_2 = str(user_cache.get_hash(message.from_user.id, 'phone'))
    tickets_str = manipulate_string(
        str(users_db.fetch_all("SELECT tickets FROM users WHERE phone = '" + query_string_2 + "'")))

    kb = [types.KeyboardButton(text="На головну🏠")]
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

    search_result = manipulate_string(
        users_db.fetch_all("SELECT tickets FROM users WHERE phone = '" + message.text + "'"))

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
    # Init of PostgreSQL database
    users_db_columns = {
        'id': 'SERIAL PRIMARY KEY',
        'phone': 'TEXT NOT NULL UNIQUE',
        'password': 'TEXT',
        'is_admin': 'BOOLEAN DEFAULT FALSE',
        'tickets': "TEXT DEFAULT '-'"
    }
    users_db.create_table(table_name='users', columns=users_db_columns)

    # Init of CouchDB database
    flights_db.create_database(db_name='flights')
    flights_db.clear_database(db_name='flights')
    couchID = flights_db.push_example_data(db_name='flights')

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
