import os
import gc
import asyncio
import tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from .parser import load_chat, parse_messages, parse_users
from .graph_builder import compute_median_delta, build_graph
from .metrics import compute_metrics, compute_interaction_strengths
from .visualization import visualize_graph, visualize_graph_html
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
    workdir = tempfile.mkdtemp(prefix='tgdocs_')
    file = await message.document.download(destination_dir=workdir)
    file_path = os.path.join(workdir, file.name)
    asyncio.create_task(process_document(message, file_path, workdir))


async def process_document(message: types.Message, file_path: str, workdir: str) -> None:
    data = load_chat(file_path)
    messages = parse_messages(data)
    users = parse_users(data)
    user_map = {u.id: (u.name or u.username or 'Unknown') for u in users}
    username_map = {u.username: (u.name or u.username) for u in users if u.username}
    del data  # free memory early

    median = compute_median_delta(messages)
    G = build_graph(messages, median, user_map, username_map)
    metrics = compute_metrics(G)
    strengths = compute_interaction_strengths(G)

    graph_path = os.path.join(workdir, 'graph.png')
    html_path = os.path.join(workdir, 'graph.html')
    pdf_path = os.path.join(workdir, 'report.pdf')
    visualize_graph(G, metrics, graph_path)
    visualize_graph_html(G, html_path)
    build_pdf(graph_path, metrics, strengths, pdf_path)
    with open(graph_path, 'rb') as img:
        await message.reply_document(img, caption='Граф взаимодействий')
    with open(html_path, 'rb') as doc:
        await message.reply_document(doc, caption='Интерактивный граф (HTML)')
    with open(pdf_path, 'rb') as doc:
        await message.reply_document(doc, caption='Подробный отчёт')
    for fname in (file_path, graph_path, html_path, pdf_path):
        try:
            os.remove(fname)
        except FileNotFoundError:
            pass
    try:
        os.rmdir(workdir)
    except OSError:
        pass
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
