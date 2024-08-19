import asyncio #Імпорти
import logging
import sys
from typing import Any, Dict
import requests
import json
import schedule 
import time
import datetime
import sqlite3
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.methods import SendMessage
from aiogram.types import FSInputFile, BufferedInputFile
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    ContentType
)

form_router = Router() #Роутер

conn = sqlite3.connect("data.db")#Database
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS perspect (
    id      INTEGER PRIMARY KEY AUTOINCREMENT
                    UNIQUE
                    NOT NULL
                    DEFAULT (1),
    url     TEXT,
    time    TEXT    NOT NULL,
    caption TEXT    NOT NULL,
    who     INTEGER,
    [where] INTEGER
);""")

user_id = None
scheduler = AsyncIOScheduler()

with open('settings.json', 'r') as json_file: #Вигрузка з конфігу та визначення змінних
    config = json.load(json_file)
TOKEN = config['TOKEN']
group_id = config['CHANNEL_ID']
allowed_users = config['ALLOWED_USERS']
path_to_photo = config['PATH_TO_PHOTO']
path_to_video = config['PATH_TO_VIDEO']
path_to_gif = config['PATH_TO_GIF']
admin = config['ADMIN_USER']

class Form(StatesGroup): #Клас зі стейтами
    AddUser = State()
    ChangeURL = State()

    ChangeURLPhoto = State()
    ChangeURLVideo = State()
    ChangeURLGif = State()

    ChangeID = State()
    DelUser = State()

    text = State()
    photo = State()
    time = State()
    check_state = State()

kb_photo = [[KeyboardButton(text="Пропустити")]] #Клавіатура для пропуску фото
photo_keyboard = ReplyKeyboardMarkup(keyboard=kb_photo, resize_keyboard=True, one_time_keyboard=True)

def admin_kb(): #Адмінська клавіатура
    kb_admin = [
        [InlineKeyboardButton(text="➕ Додати користувача в бота", callback_data='AddUser')],
        [InlineKeyboardButton(text="🆔 Змінити ID каналу", callback_data='ChangeID')],
        [InlineKeyboardButton(text="🔗 Змінити шлях до медіа-ресурсів", callback_data='ChangePath')],
        [InlineKeyboardButton(text="❌ Видалити користувача", callback_data='DelUser')],
        [InlineKeyboardButton(text="🔄 Перезапустити бота", callback_data='Restart')],
        [InlineKeyboardButton(text="◀️ Повернутися в головне меню", callback_data='MainMenu')]
    ]
    keyboard_admin = InlineKeyboardMarkup(inline_keyboard=kb_admin)
    return keyboard_admin

def kb_back():
    back = [
        [InlineKeyboardButton(text="◀️ Назад", callback_data='Back')]
    ]
    keyboard_back = InlineKeyboardMarkup(inline_keyboard=back)
    return keyboard_back

def kb_with_path(): #Клава для зміни шляхів
    kb_path = [
        [InlineKeyboardButton(text="📷 Змінити шлях до фото", callback_data='ChangePathToPhoto')],
        [InlineKeyboardButton(text="📹 Змінити шлях до відео", callback_data='ChangePathToVideo')],
        [InlineKeyboardButton(text="🌀 Змінити шлях до анімацій", callback_data='ChangePathToGif')],
        [InlineKeyboardButton(text="◀️ Назад", callback_data='Back')]
    ]
    keyboard_path = InlineKeyboardMarkup(inline_keyboard=kb_path)
    return keyboard_path

def check_data(): #Клавіатура для перевірки данних
    kb_list = [
        [InlineKeyboardButton(text="✅Все вірно", callback_data='correct')],
        [InlineKeyboardButton(text="❌Заповнити спочатку", callback_data='incorrect')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def start_message(): #Cтартова клавіатура
    kb_start = [
        [InlineKeyboardButton(text="✍️Створити пост", callback_data='create_post')]
    ]
    keyboard_start = InlineKeyboardMarkup(inline_keyboard=kb_start)
    return keyboard_start

def get_path_to_file(file_type: str): #Отримуємо шлях до медіа з конфігу
    with open('settings.json', 'r') as f:
        config = json.load(f)
    return config.get(f'PATH_TO_{file_type.upper()}')

def save_config(config): #Завантаження в конфіг
    with open("settings.json", 'w') as json_file:
        json.dump(config, json_file, indent=4)

def telegraph_file_upload(path_to_file):  #Завантаження медіа на телеграф
    '''
    Sends a file to telegra.ph storage and returns its url
    Works ONLY with 'gif', 'jpeg', 'jpg', 'png', 'mp4' 
    
    Parameters
    ---------------
    path_to_file -> str, path to a local file
    
    Return
    ---------------
    telegraph_url -> str, url of the file uploaded

    >>>telegraph_file_upload('test_image.jpg')
    https://telegra.ph/file/16016bafcf4eca0ce3e2b.jpg    
    >>>telegraph_file_upload('untitled.txt')
    error, txt-file can not be processed
    '''
    file_types = {'gif': 'image/gif', 'jpeg': 'image/jpeg', 'jpg': 'image/jpg', 'png': 'image/png', 'mp4': 'video/mp4'}
    file_ext = path_to_file.split('.')[-1]
    
    if file_ext in file_types:
        file_type = file_types[file_ext]
    else:
        return f'error, {file_ext}-file can not be proccessed' 
      
    with open(path_to_file, 'rb') as f:
        url = 'https://telegra.ph/upload'
        response = requests.post(url, files={'file': ('file', f, file_type)}, timeout=20)
    
    telegraph_url = json.loads(response.content)
    telegraph_url = telegraph_url[0]['src']
    telegraph_url = f'https://telegra.ph{telegraph_url}'
    return telegraph_url

async def load_config():
    with open('settings.json', 'r') as json_file:
        return json.load(json_file)

async def on_startup(bot: Bot) -> None:
    cursor.execute("SELECT DISTINCT who FROM perspect")
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(user_id, "Добрий ранок! Починаємо працювати")
        except Exception as e:
            bot.send_message(admin, f"Не вдалось відправити повідомлення {user_id}. Причина: <code>{e}</code>")

async def cmd_start(message: Message, state: FSMContext): #Функція для очистки State в разі якогось некоректного вводу
    await state.clear()

async def change_url(message: Message, state: FSMContext, config_key: str, allowed_extensions: list) -> None:
    try:
        url_to_file = message.text.strip()
        if not url_to_file or not os.path.splitext(url_to_file)[1] in allowed_extensions:
            await message.answer("Ви ввели некоректний шлях. Будь ласка, спробуйте ще раз.")
            return

        config[config_key] = url_to_file
        save_config(config)
        await message.answer(f"Шлях оновлено")
        await message.answer("<b>Оберіть дію</b>", reply_markup=admin_kb())
        await state.clear()
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: {config_key}_ERR.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")

async def shledude_sender_for_database(message_id: int, bot: Bot, url: str, timestamp: datetime, caption: str, who: int):
    try:
        # Загружаем актуальный конфигурационный файл
        config = await load_config()
        location = config.get('CHANNEL_ID')
        
        if url:
            await bot.send_message(chat_id=location, text=f"<a href='{url}'> </a>{caption}")
        else:
            await bot.send_message(chat_id=location, text=caption)

        cursor.execute("DELETE FROM perspect WHERE id = ?", (message_id,))
        conn.commit()
    except Exception as e:
        cursor.execute("DELETE FROM perspect WHERE id = ?", (message_id,))
        conn.commit()
        await bot.send_message(chat_id=who, text=f"Виникла помилка: <code>{e}</code>. <b>ID: 2.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel)")

def shledude_sender_for_check_database(message_id: int, url: str, timestamp: datetime, caption: str, who: int, bot: Bot):
    scheduler.add_job(shledude_sender_for_database, "date", run_date=timestamp, args=(message_id, bot, url, timestamp, caption, who))

@form_router.message(lambda message: message.chat.id not in allowed_users) #Відкидування нелегалів
async def unsuccessful_enter(message: Message):
    try:
        await message.answer("У вас немає доступу до данного боту. Якщо виникла помилка - зверніться будь ласка до @Zakhiel")
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 3.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel", parse_mode="HTML")


@form_router.message(CommandStart()) #Хендлер старт
async def starting_message(message: Message) -> None:
    try:
        await message.answer("Оберіть будь ласка дію, яку бажаєте зробити", reply_markup=start_message())
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 4.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")

@form_router.message(Command("cancel")) #Хендлер cancel
async def starting_message(message: Message, state: FSMContext) -> None:
    try:
        await state.clear()
        await message.answer("Дію успішно скасовано", reply_markup=start_message())
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 5.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(lambda message: message.chat.id in admin, Command("admin")) #Адмінський хендлер
async def unsuccessful_enter(message: Message):
    try:
        await message.answer("<b>Оберіть дію</b>", reply_markup=admin_kb())
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 6.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'AddUser') #SET STATE FOR ADD USER
async def command_add_user(call: CallbackQuery, state: FSMContext) -> None:
    try:
        await call.message.delete()
        await state.set_state(Form.AddUser)
        await call.message.answer("Надішліть мені ID користувача, якого хочете додати", reply_markup=kb_back())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 7.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'ChangeID') #SET STATE FOR CHANGE ID
async def command_add_user(call: CallbackQuery, state: FSMContext) -> None:
    try:
        await call.message.delete()
        await state.set_state(Form.ChangeID)
        await call.message.answer(f"Надішліть мені ID групи, в якій Вам потрібно надсилати повідомлення. \n \n <b>Поточний ID: {config['CHANNEL_ID']}</b>", reply_markup=kb_back())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 8.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'ChangePath') #SET STATE FOR CHANGE PATH
async def command_change_path(call: CallbackQuery, state: FSMContext) -> None:
    try: 
        await call.message.delete()
        await call.message.answer("Оберіть який шлях ви бажаєте змінити", reply_markup=kb_with_path())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 9.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")

@form_router.callback_query(lambda call: call.data == 'ChangePathToPhoto') #SET STATE FOR CHANGE PATH PHOTO
async def command_change_path_to_photo(call: CallbackQuery, state: FSMContext) -> None:
    try: 
        await call.message.delete()
        await state.set_state(Form.ChangeURLPhoto)
        path = get_path_to_file('photo')
        await call.message.answer(f"Надішліть мені шлях в форматі: <b>Path/To/Photo.png</b>\n\n<b>Поточний шлях: </b><code>{path}</code>", reply_markup=kb_back())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 10.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'ChangePathToVideo') #SET STATE FOR CHANGE PATH VIDEO
async def command_change_path_to_video(call: CallbackQuery, state: FSMContext) -> None:
    try: 
        await call.message.delete()
        await state.set_state(Form.ChangeURLVideo)
        path = get_path_to_file('video')
        await call.message.answer(f"Надішліть мені шлях в форматі: <b>Path/To/Video.mp4</b>\n\n<b>Поточний шлях: </b><code>{path}</code>", reply_markup=kb_back())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 11.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")    

@form_router.callback_query(lambda call: call.data == 'ChangePathToGif') #SET STATE FOR CHANGE PATH GIF
async def command_change_path_to_gif(call: CallbackQuery, state: FSMContext) -> None:
    try: 
        await call.message.delete()
        await state.set_state(Form.ChangeURLGif)
        path = get_path_to_file('gif')
        await call.message.answer(f"Надішліть мені шлях в форматі: <b>Path/To/Animation.gif</b>\n\n<b>Поточний шлях: </b><code>{path}</code>", reply_markup=kb_back())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 12.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")    

@form_router.callback_query(lambda call: call.data == 'DelUser') #SET STATE FOR DELETE USER
async def command_change_path(call: CallbackQuery, state: FSMContext) -> None:
    try:
        await call.message.delete()
        await state.set_state(Form.DelUser)
        await call.message.answer("Надішліть мені ID користувача, якого треба видалити", reply_markup=kb_back())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 13.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'MainMenu') #GO TO MAIN MENU
async def command_change_path(call: CallbackQuery) -> None:
    try:
        await call.message.delete()
        await call.message.answer("Ви перейшли в головне меню", reply_markup=start_message())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 14.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'Back') #GO TO BACK ADMIN MENU
async def command_change_path(call: CallbackQuery) -> None:
    try:
        await call.message.delete()
        await call.message.answer("Назад", reply_markup=admin_kb())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 15.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'Restart') #RESTART SYSTEM
async def command_restart(call: CallbackQuery) -> None:
    try:
        await call.message.delete()
        await call.message.answer("Перезапускаємо сервер")
        os.system("shutdown /r /t 0")
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 16.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(Form.AddUser, F.text) #ADDING USER
async def command_add_user(message: Message, state: FSMContext) -> None:
    try:
        if not message.text.isdigit():
            await message.answer("Введіть числове значення")
            return

        User = int(message.text)
        if User in config['ALLOWED_USERS']:
            await message.answer("Цей користувач вже є у списку дозволених.")
            return
        else:
            await message.answer(f"Користувача успішно додано")
            await message.answer("<b>Оберіть дію</b>", reply_markup=admin_kb())
            allowed_users.append(User)
            with open("settings.json", 'w') as json_file:
                json.dump(config, json_file, indent=4)
            await state.clear()
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 17.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")

@form_router.message(Form.ChangeID, F.text) #CHANGE GROUP ID
async def command_change_id(message: Message, state: FSMContext) -> None:
    try:
        if not message.text.lstrip('-').isdigit():
            await message.answer("Введіть числове значення")
            return
        IdChannel = int(message.text)
        if IdChannel == int(config['CHANNEL_ID']):
            await message.answer("Цей ID вже є в базі, спробуйте ввести інший")
            return
        else: 
            config['CHANNEL_ID'] = str(IdChannel)
            save_config(config)
            await message.answer(f"ID групи успішно змінено")
            await message.answer("<b>Оберіть дію</b>", reply_markup=admin_kb())
            await state.clear()
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 18.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")                

@form_router.message(Form.ChangeURLPhoto, F.text)  # CHANGE PATH TO PHOTO
async def command_change_url_photo(message: Message, state: FSMContext) -> None:
    try:
        await change_url(message, state, 'PATH_TO_PHOTO', ['.png', '.jpg', '.jpeg'])
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 19.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")                

@form_router.message(Form.ChangeURLVideo, F.text)  # CHANGE PATH TO VIDEO
async def command_change_url_video(message: Message, state: FSMContext) -> None:
    try:
        await change_url(message, state, 'PATH_TO_VIDEO', ['.mp4'])
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 20.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel") 

@form_router.message(Form.ChangeURLGif, F.text)  # CHANGE PATH TO GIF
async def command_change_url_gif(message: Message, state: FSMContext) -> None:
    try:
        await change_url(message, state, 'PATH_TO_GIF', ['.gif'])
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 21.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel") 

@form_router.message(Form.DelUser, F.text) #DELETE USER
async def command_add_user(message: Message, state: FSMContext) -> None:
    try:
        if not message.text.isdigit():
            await message.answer("Введіть числове значення")
            return
        UserDel = int(message.text)
        if UserDel not in config['ALLOWED_USERS']:
            await message.answer("Цього користувача немає у списку дозволених.")
            return
        else:
            await message.answer(f"Користувача успішно видалено")
            await message.answer("<b>Оберіть дію</b>", reply_markup=admin_kb())
            allowed_users.remove(UserDel)
            with open("settings.json", 'w') as json_file:
                json.dump(config, json_file, indent=4)
            await state.clear()
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 22.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.callback_query(lambda call: call.data == 'create_post') #CREATE POST
async def command_start_handler(call: CallbackQuery, state: FSMContext) -> None:
    try:
        await call.message.delete()
        await state.set_state(Form.text)
        await call.message.answer("Надішліть мені текст, який хочете розмістити на каналі", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 23.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(Form.text, F.text) #Зчитування тексту
async def process_name(message: Message, state: FSMContext) -> None:
    try:
        text = message.html_text
        prohibited = set('/$%^\\[]+=`~<>|')

        if any(char in prohibited for char in message.text): #Перевірка на заборонені символи
            await message.answer("У вас в тексті наявні заборонені символи. Спробуйте будь ласка знову")
            await state.set_state(Form.text)
            return

        await state.update_data(text=text)
        await state.set_state(Form.photo)
        await message.answer(f"{text}")
        await message.answer("Будь ласка, відправте фото/відео/анімацію, яку бажаєте прикріпити до публікації. Якщо медіафайл не треба - натисність <b>'Пропустити'</b>", reply_markup=photo_keyboard)
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 24.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(Form.text, F.content_type != ContentType.TEXT) #Хендлер для НЕ тексту
async def error_text(message: Message) -> None:
    try:
        await message.answer("Будь ласка, відправте текст")
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 25.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(F.text.lower() == ('пропустити'), Form.photo) #Хендлер для скіпання фото
async def start_questionnaire_process(message: Message, state: FSMContext):
    try:
        await message.answer("Публікація буде відправлена без медіафайлу")
        await state.update_data(photo=None)
        await state.set_state(Form.time)
        await message.answer("Введіть дату та час публікації в форматі 10 08 10 00 (10 серпня 10:00)", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 26.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(
        lambda message: message.content_type in [
            ContentType.ANIMATION, 
            ContentType.VIDEO, 
            ContentType.PHOTO
            ]
            , Form.photo)

async def start_questionnaire_process(message: Message, state: FSMContext):
    try:
        file_id = None
        try:
            if message.photo:
                file_id = message.photo[-1].file_id
                path = get_path_to_file('photo')
            elif message.video:
                file_id = message.video.file_id
                path = get_path_to_file('video')
            elif message.animation: 
                file_id = message.animation.file_id
                path = get_path_to_file('gif')
            else:
                await message.answer("Будь ласка, надішліть фото, відео або анімацію.")
                return

            #Отримуємо інфу про файл
            file_info = await message.bot.get_file(file_id)
            file_size = file_info.file_size


            # Перевіряємо його розмір
            if file_size >= 5 * 1024 * 1024:  # 5 МБ в байтах
                await message.answer("Файл занадто великий. Будь ласка, надішліть файл розміром не більше 5 МБ.")
                return
            
            # Завантажуємо на сервак
            await message.bot.download_file(file_info.file_path, destination=path)
            url = telegraph_file_upload(path)
            await state.update_data(photo=url)

            await state.set_state(Form.time)
            await message.answer("Введіть дату та час публікації в форматі 10 08 10 00 (10 серпня 10:00)", reply_markup=ReplyKeyboardRemove())
        except:
            await message.answer("Помилка при завантаженні файлу. Спробуйте будь ласка інший")
            return
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 27.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(
    lambda message: message.content_type in [
        ContentType.TEXT,
        ContentType.STICKER,
        ContentType.DOCUMENT, #Хендлер для НЕ медіа данних
        ContentType.AUDIO, 
        ContentType.VOICE 
    ],
    Form.photo)
async def start_questionnaire_process(message: Message, state: FSMContext):
    try:
        await message.answer('Будь ласка, відправте фото,відео або анімацію!')
        await state.set_state(Form.photo)
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 28.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(F.content_type != ContentType.TEXT, Form.time) #Перевіряємо дату на коректність
async def time_sheldude(message: Message, state: FSMContext):
    try:
        await message.answer("Будь ласка, введіть коректну дату в форматі '<b>день місяць година хвилина</b>'.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.time)
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 29.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")        

@form_router.message(F.content_type == ContentType.TEXT, Form.time) #Хендлер для коректної дати
async def time_sheldude(message: Message, state: FSMContext):
    try:
        try:
            timer = message.text
            year = datetime.datetime.now().year #Ще купа змінних

            day, month, hour, minute = map(int, timer.split())
            
            year = datetime.datetime.now().year
            user_datetime = datetime.datetime(year, month, day, hour, minute)

            now = datetime.datetime.now()

            data = await state.get_data()
            caption = data.get("text")

            if user_datetime < now + datetime.timedelta(minutes=1): #Перевіряємо співпадіння часу
                await message.answer("Час планування публікації повинен бути як мінімум на 1 хвилину більше від часу поточного")
                    
            else:
                await state.update_data(datetime=user_datetime)
                await state.update_data(time=user_datetime)
                await message.answer(f"Публікація буде запланована <b>{user_datetime}</b> ") #Плануємо на потрібний час публікацію
                await message.answer("<b>Перевірте чи все вірно</b>")
                if data.get("photo") != None:
                    #url = telegraph_file_upload(path) Стара строка, потім видалю як перевірю чи пофіксився баг
                    url = data.get("photo")
                    await message.answer(f"<a href='{url}'> </a>{caption}", parse_mode="HTML", reply_markup=check_data())
                elif data.get("photo") == None:
                    await message.answer(f"{caption}", parse_mode="HTML", reply_markup=check_data())

                await state.set_state(Form.check_state)
                    
        except ValueError: #Просто ексепшн
            await message.answer("Будь ласка, введіть коректну дату в форматі '<b>день місяць година хвилина</b>'.")
            await state.set_state(Form.time)
    except Exception as e:
        await message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 30.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")

@form_router.callback_query(F.data == 'correct', Form.check_state) #Якщо коррект, то плануємо наше повідомлення
async def start_questionnaire_process(call: CallbackQuery, bot: Bot, state: FSMContext):
    try:

        await call.answer('Дані збережено')
        data = await state.get_data()

        caption = data.get("text")
        run_date = data.get("time")
        url = data.get("photo")

        user_id = call.from_user.id

        await call.message.edit_reply_markup(reply_markup=None)
        
        sent_message = await call.message.answer(f'Пост заплановано на <b>{run_date}</b>.')
        message_id = sent_message.message_id

        cursor.execute("""INSERT INTO perspect (id, url, time, caption, who, [where]) VALUES (?,?,?,?,?,?)""", (message_id, url, run_date, caption, user_id, group_id,))
        conn.commit()

        await call.message.answer("Оберіть будь ласка дію, яку бажаєте зробити", reply_markup=start_message())
        
        shledude_sender_for_check_database(message_id, url, run_date, caption, user_id, bot)
        await state.clear()
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 31.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")

@form_router.callback_query(F.data == 'incorrect', Form.check_state) #Якщо не коррект - по новій
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer('Починаємо знову')
        await call.message.edit_reply_markup(reply_markup=None)
        await state.clear()
        await call.message.answer('Надішліть мені текст, який хочете розмістити на каналі')
        await state.set_state(Form.text)
    except Exception as e:
        await call.message.answer(f"Виникла помилка: <code>{e}</code>. <b>ID: 32.</b> Задля її вирішення, будь ласка, зв'яжіться з @Zakhiel")

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(form_router)
    scheduler.start()

    dp.startup.register(on_startup)

    async def process_perspect():
        cursor.execute("SELECT * FROM perspect ORDER BY time ASC")
        rows = cursor.fetchall()

        for row in rows:
            message_id, url, timestamp_str, caption, who, location = row
            timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

            if timestamp < datetime.datetime.now():
                cursor.execute("DELETE FROM perspect WHERE id = ?", (message_id,))
                conn.commit()
                await bot.send_message(int(who), f"Повідомлення, заплановане на <b>{timestamp_str}</b> видалено з бази через прострочку. Будь ласка, заплануйте повідомлення знову")

            else:
                job_id = f"job_{message_id}"
                if not scheduler.get_job(job_id):

                    scheduler.add_job(
                        shledude_sender_for_database,
                        "date",
                        run_date=timestamp,
                        args=[message_id, bot, url, timestamp, caption, who],
                        id=job_id
                    )
                    print(f"Задача для повідомлення з ID {message_id} додана в розклад публікацій.")

    await process_perspect()

    await dp.start_polling(bot)

if __name__ == "__main__": #І запускаємо Ійого
    logging.basicConfig(filename="logs.txt",
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

    logging.info("Running Logging")

    logger = logging.getLogger('Logger')

    asyncio.run(main())
