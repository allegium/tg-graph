import os
from aiogram import Bot, Dispatcher, executor, types
from .parser import load_chat, parse_messages
from .graph_builder import compute_median_delta, build_graph
from .metrics import compute_metrics
from .visualization import visualize_graph
from .report import build_pdf

TOKEN = os.getenv('TG_BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    file = await message.document.download(destination_dir='.')
    data = load_chat(file.name)
    messages = parse_messages(data)
    median = compute_median_delta(messages)
    G = build_graph(messages, median)
    metrics = compute_metrics(G)
    visualize_graph(G, metrics, 'graph.png')
    build_pdf('graph.png', metrics, 'report.pdf')
    with open('report.pdf', 'rb') as doc:
        await message.reply_document(doc)


def main():
    executor.start_polling(dp)


if __name__ == '__main__':
    main()
