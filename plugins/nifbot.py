from slackbot import settings
from slackbot.bot import listen_to
from slackbot.bot import respond_to
from slackbot.dispatcher import Message
from lib.nifbot.help import Help
from lib.nifbot.company_user import CompanyUser
import logging


@respond_to('help')
def help(message: Message):
    logging.info(message.body)

    Help().default(message)


@respond_to('(.*)')
def mention_handler(message: Message, mention_str):
    logging.info(message.body)
    words = mention_str.strip().replace("　", " ").split()
    logging.info(words)

    if len(words) == 0:
        message.reply("何かしゃべってくださいよ！")
        return

    CompanyUser().search(message, words)
