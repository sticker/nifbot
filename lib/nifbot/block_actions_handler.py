import logging
from slack.errors import SlackApiError
from lib.knowledge.watson_discovery import WatsonDiscovery


class BlockActionsHandler:
    def __init__(self):
        self.watson_discovery = WatsonDiscovery()

    def nifbot_knowledge_feedback_ok(self, slack, action):
        return self.feedback_process(slack, action, "nifty_happy", 10)

    def nifbot_knowledge_feedback_ng(self, slack, action):
        return self.feedback_process(slack, action, "nifbot", 0)

    def feedback_process(self, slack, action, reaction_emoji, relevance):
        try:
            # リクエストしたユーザ名
            slack_name = slack.event_user_name

            value = action["value"]
            action_id = action["action_id"]
            logging.info(f"{slack_name} が {value} の {action_id} ボタンをクリックしました")

            query_id = action["value"].split('__')[0]
            document_id = action["value"].split('__')[1]
            cross_reference = ""

            # Watson Discovery のトレーニングデータに登録する
            result = self.watson_discovery.create_training_example(query_id, document_id, cross_reference, relevance)

            if result is True:
                # 元のメッセージにリアクションをつける
                slack.reactions_add(reaction_emoji, slack.event_channel, slack.event_event_ts)
        except SlackApiError as e:
            # すでに同じリアクション絵文字がついている場合は already_reacted のエラーが返る
            logging.info(f"SlackApiでエラー応答がありました [{e.response['error']}]")
        except:
            logging.error("Watson Discoveryのフィードバック処理で例外が発生しました")
            import traceback
            traceback.print_exc()
            return None

        return