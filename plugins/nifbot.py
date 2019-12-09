import re
from slackbot import settings
from slackbot.bot import listen_to
from slackbot.bot import respond_to
from slackbot.dispatcher import Message
from lib.nifbot.help import Help
from lib.nifbot.company_user import CompanyUser
from lib.nifbot.company_commodity import CompanyCommodity
from lib.nifbot.akashi import Akashi
from lib.akashi.stamps import Stamps
import logging


company_user = CompanyUser()
company_commodity = CompanyCommodity()
akashi = Akashi()


@respond_to('.*')
def mention_handler(message: Message):
    logging.info(message.body)
    text = message.body['text']
    words = text.strip().replace("　", " ").replace(",", " ").replace("\n", " ").split()
    logging.info(words)

    if len(words) == 0:
        message.reply("何かしゃべってくださいよ！")
        return

    # Help
    if 'help' in words:
        Help().default(message)
        return

    # AKASHI トークン登録
    if 'token' in words:
        token_words = [s for s in words if re.match('[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}', s)]
        if len(token_words) > 0:
            akashi.token(message, token_words[0])
            return

    # AKASHI 出勤打刻
    stamps_begin_words = [s for s in words if re.match('^出社$|^出勤$|^おはよ.*$', s)]
    if len(stamps_begin_words) > 0:
        response = akashi.begin(message)
        return

    # AKASHI 退勤打刻
    stamps_finish_words = [s for s in words if re.match('^退社$|^退勤$|^帰る$|^さよなら$|^おつかれ.*$|^ばい.*$', s)]
    if len(stamps_finish_words) > 0:
        response = akashi.finish(message)
        return

    # 課金コード（7桁数字）が含まれていれば商品マスタを検索
    charge_codes = [s for s in words if re.match('[0-9]{7}', s)]
    if len(charge_codes) > 0:
        # 商品マスタを検索
        hit_count = company_commodity.search(message, charge_codes)
        if hit_count > 0:
            return

    # 社員マスタを検索
    hit_count = company_user.search(message, words)
    if hit_count == 0:
        message.reply("ちょっと何言ってるかわからないです...")
