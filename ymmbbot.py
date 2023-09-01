import datetime
from asyncio import get_event_loop, sleep
from io import BytesIO
from warnings import filterwarnings
import pylast
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from yandex_music import ClientAsync as Client
from aiogram.types import *
import config
from limited import LimitedDict
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram import Router
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = config.BOT_TOKEN
YANDEX_MUSIC_TOKEN = config.YANDEX_MUSIC_TOKEN
YOUR_CHANNEL = config.YOUR_CHANNEL
LASTFM_API_KEY = config.LASTFM_API_KEY
LASTFM_API_SECRET = config.LASTFM_API_SECRET
LASTFM_USERNAME = config.LASTFM_USERNAME
USERS = []
CACHE = LimitedDict(limit=5)
router = Router(name=__name__)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(router)

client = Client(YANDEX_MUSIC_TOKEN)
try:
    network = pylast.LastFMNetwork(
        api_key=LASTFM_API_KEY, api_secret=LASTFM_API_SECRET)
    last_fm_connected = True
except Exception:
    last_fm_connected = False

filterwarnings("ignore", category=DeprecationWarning)


async def get_track_bytes() -> bytes:
    if last_track.id not in CACHE:
        CACHE[last_track.id] = await last_track.download_bytes_async()
    return CACHE[last_track.id]


async def get_music():
    global last_track
    while True:
        if last_fm_connected:
            try:
                queues = await client.queues_list()
                last_queue = await client.queue(queues[0].id)
                last_track_id = last_queue.get_current_track()
                last_track = await last_track_id.fetch_track_async()
            except Exception:
                user = network.get_user(LASTFM_USERNAME)
                now_playing = user.get_now_playing()
                try:
                    artist = now_playing.get_artist().get_name()
                    title = now_playing.get_title()
                    searching_track = await client.search(f'{artist} {title}')
                    last_track = searching_track['best']['result']
                except Exception:
                    recent_tracks = user.get_recent_tracks(limit=1)
                    track = recent_tracks[0].track
                    artist = track.artist.name
                    title = track.title
                    searching_track = await client.search(f'{artist} {title}')
                    last_track = searching_track['best']['result']
        else:
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
        await sleep(10)
        print('хуй')


async def get_channel_message() -> str:
    try:
        artists = ', '.join(last_track.artists_name())
    except NameError:
        return ""
    title = last_track.title
    message = f"Слушает сейчас: {artists} - {title}."

    return message


async def get_imguri(last_track) -> str:
    img_uri = f"https://{last_track.cover_uri[:-2]}1000x1000"
    return img_uri


async def get_artist(last_track) -> str:
    artists = ', '.join(last_track.artists_name())
    return artists


async def get_downloadlink(last_track) -> str:
    download_info = await last_track.get_download_info_async(get_direct_links=True)
    direct_link = download_info[0].direct_link
    return direct_link


async def get_artists(last_track) -> str:
    artists = ', '.join(last_track.artists_name())
    return artists


async def get_trackid(last_track) -> str:
    last_track_id = last_track.track_id
    result = last_track_id.split(':')[0]
    return result


async def send_message_every_minute() -> None:
    while True:
        message_text = await get_channel_message()
        try:
            last_track_id = await get_trackid(last_track)
        except NameError:
            await sleep(3)
            continue
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text='В ЛС', url=YOUR_URL)
        )
        builder.add(types.InlineKeyboardButton(
            text='Остальные площадки', url=f'https://song.link/ya/{last_track.id}')
        )
        builder.add(types.InlineKeyboardButton(
            text='В ЛС', url=f'https://music.yandex.ru/track/{last_track.id}')
        )
        for user in USERS:
            chat_id = user['chat_username']
            message_id = user['message_id']
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message_text_with_time = f"{message_text}\nВремя: {current_time}\n\nBOT CREATED BY MIPOHBOPOHIH"
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text_with_time,
                                        reply_markup=builder.as_markup())
        await sleep(10)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    message_reply = await message.reply('В процессе..')
    img_uri = await get_imguri(last_track)
    artist = await get_artists(last_track)
    title = last_track.title
    duration_ms = last_track.duration_ms // 1000
    file_name = f'{artist} - {title}.mp3'
    raw_audio = await get_track_bytes()
    audio = BufferedInputFile(raw_audio, filename=file_name)
    audio.name = file_name
    await bot.send_audio(message.chat.id, title=title, performer=artist, duration=duration_ms, thumbnail=img_uri,
                         audio=audio)
    await message_reply.delete()


@router.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    builder = InlineKeyboardBuilder()
    # builder.button(text='В ЛС', url=YOUR_URL)
    builder.button(text='Остальные площадки', url=f'https://song.link/ya/{last_track.id}')
    builder.button(text='Песня в ЯМ', url=f'https://music.yandex.ru/track/{last_track.id}')
    audio = await get_downloadlink(last_track)
    artist = await get_artists(last_track)
    title = last_track.title
    duration = last_track.duration_ms // 1000
    minutes = duration // 60
    seconds = duration % 60
    duration_formatted = f"{minutes}:{seconds:02}"
    response_message = f"Ты слушаешь сейчас: {artist} - {title} ({duration_formatted})"
    result_id = '1'
    result = types.InlineQueryResultAudio(
        id=result_id,
        audio_url=audio,
        title=title,
        performer=artist,
        audio_duration=duration,
        caption=response_message,
        reply_markup=builder.as_markup()
    )

    await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)


async def on_startup(dp: Dispatcher) -> None:
    global YOUR_URL
    await client.init()
    me = await bot.get_me()
    YOUR_URL = f"https://t.me/{me.username}?start"
    message = await bot.send_message(chat_id=YOUR_CHANNEL, text='BOT CREATED BY MIPOHBOPOHIH')
    USERS.append({'chat_username': YOUR_CHANNEL,
                  'message_id': message.message_id})


async def main() -> None:
    await dp.start_polling(bot, on_startup=on_startup, loop=loop)


if __name__ == '__main__':
    loop = get_event_loop()
    loop.create_task(get_music())
    loop.create_task(send_message_every_minute())
    loop.run_until_complete(main())
