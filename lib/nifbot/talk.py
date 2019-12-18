from lib import get_logger
from lib.talk.a3rt import A3RT


class Talk:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.talk_api = A3RT()

    def talking(self, message, words):
        talking = ' '.join(words)
        res = ''
        try:
            res = self.talk_api.get(talking)
            if res != '':
                message_text = res + " :nifbot:"
                message.reply(message_text)
                self.logger.info(message_text)
                return True
            else:
                return False
        except:
            self.logger.warning("Talk APIで例外が発生しました")
            import traceback
            traceback.print_exc()
            return False
