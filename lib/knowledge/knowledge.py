from lib import get_logger
from lib.aws.kendra import Kendra
from ibm_watson import DiscoveryV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


class Knowledge:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.kendra = Kendra()
        # for IBM Watson Discovery
        apikey = 'n6ADqupB1mbr1-riI0W1HLQokOKb8tvdSrRC9sTYZSBl'
        version = '2019-04-30'
        url = 'https://api.us-south.discovery.watson.cloud.ibm.com/instances/e7d46b06-8908-44aa-bedd-123548735430'
        authenticator = IAMAuthenticator(f'{apikey}')
        self.discovery = DiscoveryV1(
            version=f'{version}',
            authenticator=authenticator
        )
        self.discovery.set_service_url(f'{url}')
        self.environment_id = '29110ef0-5c27-4a5a-b1de-dd9c8fd53147'
        self.collection_id = '27c31e05-66f3-4eb9-b0ff-b5d1cd5701f0'

    def ask(self, slack, words):
        # return self.ask_kendra(slack, words)
        # return self.ask_watson(slack, words)
        return self.interactive_test(slack)

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

    def ask_watson(self, slack, words):
        query = ' '.join(words)
        res = ''
        try:
            res = self.discovery.query(environment_id=self.environment_id, collection_id=self.collection_id,
                                       natural_language_query=query, passages=True)
            if res != '':
                text = res.get_result()['passages'][0]['passage_text']
                self.logger.info(res.get_result()['passages'][0])
                message_text = text + " :nifbot:"
                slack.reply(message_text)
                # self.logger.info(message_text)
                return True
            else:
                return False
        except:
            self.logger.warning("Watson Discoveryで例外が発生しました")
            import traceback
            traceback.print_exc()
            return False

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
