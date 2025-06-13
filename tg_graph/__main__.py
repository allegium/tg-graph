import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description='Run TG Graph bot')
    parser.add_argument('--token', help='Telegram bot token')
    args = parser.parse_args()

    if args.token:
        os.environ['TG_BOT_TOKEN'] = args.token

    from .bot import main as bot_main
    bot_main()


if __name__ == '__main__':
    main()
