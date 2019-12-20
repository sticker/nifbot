from datetime import datetime
from lib import get_logger
from slackbot.dispatcher import Message
from lib.aws.dynamodb import Dynamodb


class CompanyUserTag:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.dynamodb = Dynamodb()
        self.tablename = 'company_user_tag'

    def tag(self, message: Message, uids: list, tags: list):
        # リクエストしたユーザ名
        slack_name = message.channel._client.users[message.body['user']][u'name']
        # IDをすべて大文字化する
        uids = list(map(str.upper, uids))

        for uid in uids:
            for tag in tags:
                if self.save_tag(uid, tag, owner=slack_name):
                    message_text = f"[{uid}]に[{tag}]タグを登録しました！"
                else:
                    message_text = f"[{uid}]に[{tag}]タグの登録に失敗しました...すいません！"
                message.reply(message_text)
        return

    def tag_list(self, message: Message, uids: list):
        # リクエストしたユーザ名
        slack_name = message.channel._client.users[message.body['user']][u'name']
        # IDをすべて大文字化する
        uids = list(map(str.upper, uids))

        message_texts = list()
        for uid in uids:
            texts = [f"{uid}:"]
            tags = self.get_tags_by_uid(uid)
            if len(tags) == 0:
                texts.append("タグはついていません")
                continue

            for tag in tags:
                texts.append(f"`{tag}`")

            message_texts.append(' '.join(texts))

        message_text = '\n'.join(message_texts)
        message.reply(message_text)
        self.logger.info(message_text)
        return

    def uid_list(self, message: Message, tags: list):
        # リクエストしたユーザ名
        slack_name = message.channel._client.users[message.body['user']][u'name']

        message_texts = list()
        for tag in tags:
            texts = [f"{tag}:"]
            uids = self.get_uids_by_tag(tag)
            if len(uids) == 0:
                texts.append("このタグがついている人はいません")
                message_texts.append(' '.join(texts))
                continue

            for uid in uids:
                texts.append(f"`{uid}`")
            message_texts.append(' '.join(texts))

        message_text = '\n'.join(message_texts)
        message.reply(message_text)
        self.logger.info(message_text)
        return

    def save_tag(self, uid: str, tag: str, owner: str):
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        item = {
            'uid': uid.upper(),
            'tag': tag,
            'owner': owner,
            'created_time': now
        }
        self.logger.debug(f"タグを登録します item={item}")
        try:
            self.dynamodb.insert(target=self.tablename, item=item)
            return True
        except:
            self.logger.warning("タグの登録で例外が発生しました")
            import traceback
            traceback.print_exc()
            return False

    def get_uids_by_tags(self, tags: list):
        uids = list()
        for tag in tags:
            uids_by_tag = self.get_uids_by_tag(tag)
            if len(uids_by_tag) == 0:
                continue
            uids.extend(uids_by_tag)

        return uids

    def get_uids_by_tag(self, tag: str):
        uids = list()
        records = self.dynamodb.scan_specified_attr_value(tablename=self.tablename, attr_name='tag', attr_value=tag)
        if records is None or len(records) == 0:
            self.logger.debug(f"[{tag}]のタグがついているユーザはいませんでした")
            return uids

        for record in records:
            uids.append(record['uid'])

        return uids

    def get_tags_by_uid(self, uid: str):
        tags = list()
        records = self.dynamodb.scan_specified_attr_value(tablename=self.tablename, attr_name='uid', attr_value=uid)
        if records is None or len(records) == 0:
            self.logger.debug(f"[{uid}]にはタグがついていません")
            return tags

        for record in records:
            tags.append(record['tag'])

        return tags
