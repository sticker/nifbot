import logging


class ReactionHandler:
    def __init__(self):
        pass

    def reaction_handler(self, slack):
        # リクエストしたユーザ名
        slack_name = slack.event_user_name
        logging.info(f"{slack_name} が {slack.event_reaction} のリアクションをつけました")
