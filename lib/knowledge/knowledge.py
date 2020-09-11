from lib import get_logger
from lib.aws.kendra import Kendra
from lib.knowledge.watson_discovery import WatsonDiscovery
# from lib.knowledge.watson_assistant import WatsonAssistant


class Knowledge:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.kendra = Kendra()
        self.watson_discovery = WatsonDiscovery()
        # self.watson_assistant = WatsonAssistant()

    def ask(self, slack, words):
        # return self.ask_kendra(slack, words)
        return self.ask_watson_discovery(slack, words)
        # return self.ask_watson_assistant(slack, words)
        # return self.interactive_test(slack)

    def ask_kendra(self, slack, words):
        query = ' '.join(words)
        res = ''
        try:
            res = self.kendra.search(query)
            if res != '':

                message_text = res + " :nifbot:"
                slack.reply(message_text)
                self.logger.info(message_text)
                return True
            else:
                return False
        except:
            self.logger.warning("Kendraで例外が発生しました")
            import traceback
            traceback.print_exc()
            return False

    def ask_watson_discovery(self, slack, words):
        query = ' '.join(words)
        try:
            blocks, attachments = self.watson_discovery.query(query)
            if blocks is not None:
                self.logger.info(f"blocks={blocks}")
                self.logger.info(f"attachments={attachments}")
                slack.reply("", blocks=blocks)
                # attachmentsは一つずつ分けて投稿する（それぞれでリアクション絵文字つけられるように）
                for attachment in attachments:
                    slack.send("", attachments=[attachment])
                return True
            else:
                return False
        except:
            self.logger.warning("Watson Discoveryで例外が発生しました")
            import traceback
            traceback.print_exc()
            return False

    # def ask_watson_assistant(self, slack, words):
    #     query = ' '.join(words)
    #     res = ''
    #     try:
    #         res = self.watson_assistant.message_stateless(query)
    #         if res != '':
    #             message_text = res + " :nifbot:"
    #             slack.reply(message_text)
    #             self.logger.info(message_text)
    #             return True
    #         else:
    #             return False
    #     except:
    #         self.logger.warning("Watson Assistantで例外が発生しました")
    #         import traceback
    #         traceback.print_exc()
    #         return False

    def interactive_test(self, slack):
        attachments = [{
            "title": "ナレッジ検索機能、ほしい？",
            "callback_id": "nifbot_knowledge_like",
            "actions": [
                {
                    "id": "1",
                    "name": "ok",
                    "text": "ほしい！",
                    "type": "button",
                    "value": "1",
                    "style": "primary"
                },
                {
                    "id": "2",
                    "name": "ng",
                    "text": "いらない！",
                    "type": "button",
                    "value": "-1",
                    "style": "danger"
                },
                {
                    "id": "3",
                    "name": "none",
                    "text": "どっちでもいい",
                    "type": "button",
                    "value": "0",
                    "style": "default"
                }
            ]
        }]

        text = 'ニフティのナレッジを勉強してるよ。もうすぐ応答できるようになるから待っててね！'
        res = slack.reply(text, attachments=attachments)
        return True
