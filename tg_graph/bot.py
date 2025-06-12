import os
import gc
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from .parser import load_chat, parse_messages, parse_users
from .graph_builder import compute_median_delta, build_graph
from .metrics import compute_metrics, compute_interaction_strengths
from .visualization import visualize_graph
from .report import build_pdf

TOKEN = os.getenv('TG_BOT_TOKEN')
if not TOKEN:
    raise RuntimeError('TG_BOT_TOKEN environment variable not set')

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(
        'Привет! Я могу проанализировать историю чата Telegram. '
        'Пожалуйста, отправь мне файл экспорта чата (обычно это result.json).'
    )


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    await message.reply('Файл получен, начинаю обработку...')
    # Remove leftover files from previous runs
    for fname in ('graph.png', 'report.pdf'):
        if os.path.exists(fname):
            os.remove(fname)
    for fname in os.listdir('.'):  # clear old JSON exports
        if fname.endswith('.json'):
            try:
                os.remove(fname)
            except FileNotFoundError:
                pass

    file = await message.document.download(destination_dir='.')
    data = load_chat(file.name)
    messages = parse_messages(data)
    users = parse_users(data)
    user_map = {u.id: (u.name or u.username or u.id) for u in users}
    username_map = {u.username: (u.name or u.username) for u in users if u.username}
    del data  # free memory early

    median = compute_median_delta(messages)
    G = build_graph(messages, median, user_map, username_map)
    metrics = compute_metrics(G)
    strengths = compute_interaction_strengths(G)
    visualize_graph(G, metrics, 'graph.png')
    build_pdf('graph.png', metrics, strengths, 'report.pdf')
    with open('graph.png', 'rb') as img:
        await message.reply_document(img, caption='Граф взаимодействий')
    with open('report.pdf', 'rb') as doc:
        await message.reply_document(doc, caption='Подробный отчёт')
    os.remove(file.name)
    os.remove('graph.png')
    os.remove('report.pdf')
    del messages, users, metrics, strengths
    gc.collect()


@dp.message_handler()
async def unknown_message(message: types.Message):
    await message.reply('Извините, я понимаю только команду /start и файлы экспорта чата.')


def main():
    print('Бот запущен и ждёт файлы...')
    executor.start_polling(dp)


if __name__ == '__main__':
    main()
