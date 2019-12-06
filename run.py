import logging
from slackbot import settings
from slackbot.bot import Bot

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) {%(filename)s:%(lineno)d} %(message)s',
                    )

def main():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    print('start slackbot')
    main()

