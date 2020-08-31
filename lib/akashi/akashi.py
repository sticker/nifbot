from datetime import datetime
from lib import get_logger
from lib.aws.dynamodb import Dynamodb
from lib.akashi.stamps import Stamps
from lib.help.help import Help


class Akashi:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.dynamodb = Dynamodb()
        self.stamps = Stamps()
        self.help = Help()

    def get_akashi_token(self, slack_name):
        user = self.dynamodb.query_specified_key_value(tablename='user', key='slack_name', value=slack_name)
        if user is None or len(user) == 0:
            self.logger.debug("userレコードがありませんでした")
            return ''

        # ￿必ず1レコード取得
        return user[0]['akashi_token']

    def save_akashi_token(self, slack_name, akashi_token):
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        response = self.dynamodb.save_akashi_token(tablename='user', slack_name=slack_name,
                                                   akashi_token=akashi_token, akashi_token_save_time=now)
        self.logger.debug(response)

        # TODO: responseを見て正常異常判定
        if not response:
            return False

        return True

    def token(self, slack, akashi_token):
        # リクエストしたユーザ名
        slack_name = slack.event_user_name

        if self.save_akashi_token(slack_name, akashi_token):
            slack.reply("AKASHIのトークンを登録しました！")
        else:
            slack.reply("AKASHIのトークン登録に失敗しました...すいません！")

        return

    def begin(self, slack):

        # ￿打刻機能は一旦無効化しておきます。使える日が来たらオープンしましょう。
        slack.reply("おはようございます！AKASHIの画面で打刻してくださいね:smiling_imp:")
        return

        # リクエストしたユーザ名
        slack_name = slack.event_user_name
        akashi_token = self.get_akashi_token(slack_name)

        if akashi_token == '':
            slack.reply("AKASHIのトークンを登録してください")
            self.help.akashi_token(slack)
            return

        response_body = self.stamps.begin(akashi_token)

        if response_body["success"] == True:
            slack.reply(f"出勤打刻しました！今日もがんばろー:smile: `{response_body['response']['stampedAt']}`")
        else:
            slack.reply("出勤打刻に失敗しました...")
            self.logger.warning(f"出勤打刻に失敗しました slack_name: {slack_name}")
            self.logger.warning(response_body)

    def finish(self, slack):

        # ￿打刻機能は一旦無効化しておきます。使える日が来たらオープンしましょう。
        slack.reply("おつかれさまでした！AKASHIの画面で打刻してくださいね:smiling_imp:")
        return

        # リクエストしたユーザ名
        slack_name = slack.event_user_name
        akashi_token = self.get_akashi_token(slack_name)

        if akashi_token == '':
            slack.reply("AKASHIのトークンを登録してください")
            self.help.akashi_token(slack)
            # TODO: トークン登録IFを作成する
            return

        response_body = self.stamps.finish(akashi_token)

        if response_body["success"] == True:
            slack.reply(f"退勤打刻しました！おつかれさまでした:blush: `{response_body['response']['stampedAt']}`")
        else:
            slack.reply("退勤打刻に失敗しました...")
            self.logger.warning(f"退勤打刻に失敗しました slack_name: {slack_name}")
            self.logger.warning(response_body)
