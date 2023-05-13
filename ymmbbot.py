import asyncio
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from yandex_music import Client
import config
BOT_TOKEN = config.BOT_TOKEN
YANDEX_MUSIC_TOKEN = config.YANDEX_MUSIC_TOKEN
YOUR_CHANNEL = config.YOUR_CHANNEL
YOUR_URL = config.YOUR_URL


bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
client = Client(YANDEX_MUSIC_TOKEN)


async def get_music():
    client.init()
    queues = client.queues_list()
    last_queue = client.queue(queues[0].id)
    last_track_id = last_queue.get_current_track()
    last_track = last_track_id.fetch_track()
    return last_track
    
    
async def get_channel_message() -> str:
    last_track = await get_music()

    artists = ', '.join(last_track.artists_name())
    title = last_track.title
    message = f"Слушает сейчас: {artists} - {title}."

    return message


async def get_lyrics() -> str:
    last_track = await get_music()
    artists = ', '.join(last_track.artists_name())
    title = last_track.title
    message = f'Сейчас играет: {artists} - {title}'
    try:
        lyrics = last_track.get_lyrics('TEXT')

        lyrics = f'{message}\n\n{lyrics.fetch_lyrics()}\n\nИсточник: {lyrics.major.pretty_name}\n\nBOT CREATED BY MIPOHBOPOHIH'
    except Exception:
        lyrics = f'{message}\nТекст песни отсутствует.\n\nBOT CREATED BY MIPOHBOPOHIH'
    return lyrics


async def get_image():
    client.init()
    last_track = await get_music()
    img_uri = f"https://{last_track.cover_uri[:-2]}400x400"
    return img_uri


USERS = []


async def send_message_every_minute():
    while True:
        message_text = await get_channel_message()
        inline_btn_1 = InlineKeyboardButton('Узнать текст песни', url=YOUR_URL)
        inline_keyboard = InlineKeyboardMarkup(row_width=2).add(inline_btn_1)
        for user in USERS:
            chat_id = user['chat_username']
            message_id = user['message_id']
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message_text_with_time = f"{message_text}\nВремя: {current_time}\nBOT CREATED BY MIPOHBOPOHIH"
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text_with_time, reply_markup=inline_keyboard)
        await asyncio.sleep(15)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    lyr = await get_lyrics()
    img_uri = await get_image()
    await bot.send_photo(chat_id=message.chat.id, photo=img_uri)
    await message.reply(lyr)


async def on_startup(dp):
    message = await bot.send_message(chat_id=YOUR_CHANNEL, text='BOT CREATED BY MIPOHBOPOHIH')
    USERS.append({'chat_username': YOUR_CHANNEL, 'message_id': message.message_id})


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(send_message_every_minute())
    executor.start_polling(dp, on_startup=on_startup)
