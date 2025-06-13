import os
import threading
import tkinter as tk
from tkinter import messagebox

from tg_graph.bot import main as run_bot


def start_bot(token: str) -> None:
    os.environ['TG_BOT_TOKEN'] = token
    run_bot()


def on_start():
    token = entry.get().strip()
    if not token:
        messagebox.showerror('Error', 'Введите токен бота')
        return
    button.config(state='disabled')
    label.config(text='Бот запущен. Закройте окно для остановки.')
    threading.Thread(target=start_bot, args=(token,), daemon=True).start()

root = tk.Tk()
root.title('TG Graph Bot Launcher')
label = tk.Label(root, text='Введите токен бота и нажмите "Запустить"')
label.pack(pady=10)
entry = tk.Entry(root, width=60)
entry.pack(padx=10)
button = tk.Button(root, text='Запустить', command=on_start)
button.pack(pady=10)
root.mainloop()
