import re
from slackbot import settings
from slackbot.bot import listen_to
from slackbot.bot import respond_to
from slackbot.dispatcher import Message
from lib.nifbot.help import Help
from lib.nifbot.company_product import CompanyProduct
from lib.nifbot.company_user import CompanyUser
from lib.nifbot.company_commodity import CompanyCommodity
from lib.nifbot.akashi import Akashi
from lib.nifbot.talk import Talk
import logging

company_product = CompanyProduct()
company_user = CompanyUser()
company_commodity = CompanyCommodity()
akashi = Akashi()
talk = Talk()


@respond_to('.*')
def mention_handler(message: Message):
    logging.info(message.body)
    # リクエストしたユーザ名
    slack_name = message.channel._client.users[message.body['user']][u'name']

    text = message.body['text']
    words = text.strip().replace("　", " ").replace(",", " ").replace("\n", " ").split()
    logging.info(f"{slack_name} のリクエストを処理します words={words}")

    if len(words) == 0:
        message_text = "何かしゃべってくださいよ！"
        message.reply(message_text)
        logging.info(message_text)
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

    # どれか1件でもヒットしたらTrueにする
    hit_at_least = False

    # 課金コード（7桁数字）で商品マスタを検索
    if company_commodity.search_by_charge_code(message, words) > 0:
        hit_at_least = True

    # プロダクトコードが含まれていればプロダクトマスタを検索
    if company_product.search_by_code(message, words) > 0:
        hit_at_least = True

    # コードでの検索にヒットしてたら終了にする
    if hit_at_least:
        return

    # 社員マスタを検索
    if company_user.search(message, words) > 0:
        hit_at_least = True

    # 商品名で商品マスタを検索
    if company_commodity.search_by_name(message, words) > 0:
        hit_at_least = True

    # プロダクト名でプロダクトマスタを検索
    if company_product.search_by_name(message, words) > 0:
        hit_at_least = True

    # 1件もヒットしなかったら会話とみなす
    if not hit_at_least:
        # 会話APIで応答を返す
        if not talk.talking(message, words):
            message_text = "ちょっと何言ってるかわからないです..."
            message.reply(message_text)
            logging.info(message_text)
    return
