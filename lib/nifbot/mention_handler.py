import re
from lib.help.help import Help
from lib.company_master.company_product import CompanyProduct
from lib.company_master.company_user import CompanyUser
from lib.company_master.company_user_tag import CompanyUserTag
from lib.company_master.company_commodity import CompanyCommodity
from lib.company_master.company_group import CompanyGroup
from lib.akashi.akashi import Akashi
from lib.talk.talk import Talk
from lib.knowledge.knowledge import Knowledge
import logging


class MentionHandler:
    def __init__(self):
        self.company_product = CompanyProduct()
        self.company_user = CompanyUser()
        self.company_user_tag = CompanyUserTag()
        self.company_commodity = CompanyCommodity()
        self.company_group = CompanyGroup()
        self.akashi = Akashi()
        self.talk = Talk()
        self.knowledge = Knowledge()


    def text_to_wards(self, text):
        text = text.strip()
        # メンション部分を除外する
        text = re.sub("<@\S*>", "", text)

        # リンクがついていたら除外する
        # 例） <http://test.na|test.na> など
        text = re.sub("<[http:|https:|tel:|mailto:]\S*\||>", "", text)

        # アスタリスクがついていたら除外する
        text = text.replace("*", "")

        # 対応する区切り文字を半角スペースに統一した上でリスト化
        words = text.replace("　", " ").replace(",", " ").replace("\n", " ").split()
        return words

    def mention_handler(self, slack):
        logging.info(slack.event_text)
        # リクエストしたユーザ名
        slack_name = slack.event_user_name
        words = self.text_to_wards(slack.event_text)
        logging.info(f"{slack_name} のリクエストを処理します words={words}")

        if len(words) == 0:
            message_text = "何かしゃべってくださいよ！"
            slack.reply(message_text)
            logging.info(message_text)
            return

        # Help
        if 'help' in words:
            Help().default(slack)
            return

        # AKASHI トークン登録
        if 'token' in words:
            token_words = [s for s in words if re.match('[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}', s)]
            if len(token_words) > 0:
                self.akashi.token(slack, token_words[0])
                return

        # AKASHI 出勤打刻
        stamps_begin_words = [s for s in words if re.match('^出社$|^出勤$|^おはよ.*$', s)]
        if len(stamps_begin_words) > 0:
            response = self.akashi.begin(slack)
            return

        # AKASHI 退勤打刻
        stamps_finish_words = [s for s in words if re.match('^退社$|^退勤$|^帰る$|^さよなら$|^おつかれ.*$|^ばい.*$', s)]
        if len(stamps_finish_words) > 0:
            response = self.akashi.finish(slack)
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
                    response = self.company_user_tag.tag_rm(slack, uid_words, tag_words)
                    return
                else:
                    # 登録
                    response = self.company_user_tag.tag(slack, uid_words, tag_words)
                    return
            # IDのみの指定であれば、そのIDについているタグ一覧を表示する
            if len(uid_words) > 0 and len(tag_words) == 0:
                response = self.company_user_tag.tag_list(slack, uid_words)
                return
            # タグのみの指定であれば、そのタグがついているID一覧を表示する
            if len(uid_words) == 0 and len(tag_words) > 0:
                response = self.company_user_tag.uid_list(slack, tag_words)
                return


        # どれか1件でもヒットしたらTrueにする
        hit_at_least = False

        # 課金コード（7桁数字）で商品マスタを検索
        if self.company_commodity.search_by_charge_code(slack, words) > 0:
            hit_at_least = True

        # プロダクトコードが含まれていればプロダクトマスタを検索
        if self.company_product.search_by_code(slack, words) > 0:
            hit_at_least = True

        # 組織コードが含まれていれば組織マスタを検索
        if self.company_group.search_by_code(slack, words) > 0:
            hit_at_least = True

        # コードでの検索にヒットしてたら終了にする
        if hit_at_least:
            return

        # 社員マスタを検索
        if self.company_user.search(slack, words) > 0:
            hit_at_least = True

        # 商品名で商品マスタを検索
        if self.company_commodity.search_by_name(slack, words) > 0:
            hit_at_least = True

        # プロダクト名でプロダクトマスタを検索
        if self.company_product.search_by_name(slack, words) > 0:
            hit_at_least = True

        # 組織名で組織マスタを検索
        if self.company_group.search_by_name(slack, words) > 0:
            hit_at_least = True

        # 1件もヒットしなかったらFAQか会話とみなす
        if not hit_at_least:
            # FAQ検索
            if not self.knowledge.ask(slack, words):
                # 会話APIで応答を返す
                if not self.talk.talking(slack, words):
                    message_text = "ちょっと何言ってるかわからないです..."
                    slack.reply(message_text)
                    logging.info(message_text)
        return
