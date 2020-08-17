import re
from slackbot import settings
from slackbot.bot import listen_to
from slackbot.bot import respond_to
from slackbot.dispatcher import Message
from lib.nifbot.help import Help
from lib.nifbot.company_product import CompanyProduct
from lib.nifbot.company_user import CompanyUser
from lib.nifbot.company_user_tag import CompanyUserTag
from lib.nifbot.company_commodity import CompanyCommodity
from lib.nifbot.company_group import CompanyGroup
from lib.nifbot.akashi import Akashi
from lib.nifbot.talk import Talk
from lib.nifbot.faq import Faq
import logging

company_product = CompanyProduct()
company_user = CompanyUser()
company_user_tag = CompanyUserTag()
company_commodity = CompanyCommodity()
company_group = CompanyGroup()
akashi = Akashi()
talk = Talk()
faq = Faq()


def text_to_wards(text):
    text = text.strip()
    # リンクがついていたら除外する
    # 例） <http://test.na|test.na> など
    text = re.sub("<[http:|https:|tel:|mailto:]\S*\||>", "", text)

    # アスタリスクがついていたら除外する
    text = text.replace("*", "")

    # 対応する区切り文字を半角スペースに統一した上でリスト化
    words = text.replace("　", " ").replace(",", " ").replace("\n", " ").split()
    return words


@respond_to('.*')
def mention_handler(message: Message):
    logging.info(message.body)
    # リクエストしたユーザ名
    slack_name = message.channel._client.users[message.body['user']][u'name']
    words = text_to_wards(message.body['text'])
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

    # 社員情報のタグ制御
    if 'tag' in words:
        # IDを取得
        uid_words = [s for s in words if re.match('[a-zA-Z]{3}[0-9]{5}', s)]
        # タグを取得
        tag_words = [s for s in words if s not in uid_words and s != 'tag' and s != 'rm']
        # IDの重複を削除
        uid_words = list(dict.fromkeys(uid_words))
        # IDを大文字化する
        uid_words = list(map(str.upper, uid_words))
        # IDとタグどちらも指定があれば、タグ登録か削除処理をする
        if len(uid_words) > 0 and len(tag_words) > 0:
            if 'rm' in words:
                # 削除
                response = company_user_tag.tag_rm(message, uid_words, tag_words)
                return
            else:
                # 登録
                response = company_user_tag.tag(message, uid_words, tag_words)
                return
        # IDのみの指定であれば、そのIDについているタグ一覧を表示する
        if len(uid_words) > 0 and len(tag_words) == 0:
            response = company_user_tag.tag_list(message, uid_words)
            return
        # タグのみの指定であれば、そのタグがついているID一覧を表示する
        if len(uid_words) == 0 and len(tag_words) > 0:
            response = company_user_tag.uid_list(message, tag_words)
            return


    # どれか1件でもヒットしたらTrueにする
    hit_at_least = False

    # 課金コード（7桁数字）で商品マスタを検索
    if company_commodity.search_by_charge_code(message, words) > 0:
        hit_at_least = True

    # プロダクトコードが含まれていればプロダクトマスタを検索
    if company_product.search_by_code(message, words) > 0:
        hit_at_least = True

    # 組織コードが含まれていれば組織マスタを検索
    if company_group.search_by_code(message, words) > 0:
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

    # 組織名で組織マスタを検索
    if company_group.search_by_name(message, words) > 0:
        hit_at_least = True

    # 1件もヒットしなかったらFAQか会話とみなす
    if not hit_at_least:
        # FAQ検索
        if not faq.ask(message, words):
            # 会話APIで応答を返す
            if not talk.talking(message, words):
                message_text = "ちょっと何言ってるかわからないです..."
                message.reply(message_text)
                logging.info(message_text)
    return
