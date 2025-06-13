# tg-graph

Telegram chat interaction analyzer.

## How to run the bot

Follow these steps even if you have never written code before.

1. **Install Python**. Visit [python.org](https://www.python.org/downloads/) and download
   the latest Python 3 installer for your operating system. During installation
   make sure that the option to add Python to your `PATH` is checked.

2. **Get the project files**. Click the green “Code” button on the GitHub page
   and choose “Download ZIP”. After downloading, unzip the archive to a folder on
   your computer.

3. **Install the required libraries**. Open a terminal (on Windows you can use
   *Command Prompt*). Change to the folder with the unzipped files and run:

   ```bash
   pip install aiogram networkx matplotlib reportlab
   ```

4. **Create a Telegram bot**. In Telegram open `@BotFather`, send the command
   `/newbot` and follow the instructions. BotFather will give you a token that
   looks like a long string of letters and numbers. Keep this token handy.

5. **Set the bot token**. In the terminal run the following command, replacing
   `TOKEN` with the token you received from BotFather:

   ```bash
   export TG_BOT_TOKEN=TOKEN
   ```

   On Windows use `set` instead of `export`:

   ```cmd
   set TG_BOT_TOKEN=TOKEN
   ```

6. **Start the bot**. Still in the project folder, run:

   ```bash
   python -m tg_graph.bot
   ```

   You should see a message that the bot has started and is waiting for files.

7. **Send a chat export**. Use Telegram’s built‑in export feature to save a chat
   history as a JSON file (usually named `result.json`). Send this file to your
   bot. After the upload finishes, the bot will analyze the chat and reply first
   with a PNG image containing the interaction graph, an HTML file with an
   interactive version of the graph, and a PDF report with a structured table of
   metrics. The HTML graph highlights nodes and edges on hover, shows the
   participants of every connection and uses thicker lines for stronger
   interactions.
   Nodes without connections or with unknown names are omitted to keep the graph clear.

That’s all! Every time you restart the bot you will need to set the
`TG_BOT_TOKEN` environment variable again, so keep your token somewhere safe.
