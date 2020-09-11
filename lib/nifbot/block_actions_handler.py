import logging
from slack.errors import SlackApiError


class BlockActionsHandler:
    def __init__(self):
        pass

    def nifbot_knowledge_feedback_ok(self, slack, action):
        # TODO: nifbot_knowledge_feedback_ng() と共通化する
        # リクエストしたユーザ名
        slack_name = slack.event_user_name

        value = action["value"]
        logging.info(f"{slack_name} が {value} をクリックしました")

        # TODO: Watson Discovery のトレーニングデータに登録する

        # 元のメッセージにリアクションをつける
        try:
            slack.reactions_add("nifty_happy", slack.event_channel, slack.event_event_ts)
        except SlackApiError as e:
            # すでに同じリアクション絵文字がついている場合は already_reacted のエラーが返る
            logging.info(f"SlackApiでエラー応答がありました [{e.response['error']}]")

        return

    def nifbot_knowledge_feedback_ng(self, slack, action):
        # リクエストしたユーザ名
        slack_name = slack.event_user_name

        value = action["value"]
        logging.info(f"{slack_name} が {value} をクリックしました")

        # TODO: Watson Discovery のトレーニングデータに登録する

        # 元のメッセージにリアクションをつける
        try:
            slack.reactions_add("nifbot", slack.event_channel, slack.event_event_ts)
        except SlackApiError as e:
            # すでに同じリアクション絵文字がついている場合は already_reacted のエラーが返る
            logging.info(f"SlackApiでエラー応答がありました [{e.response['error']}]")

        return
