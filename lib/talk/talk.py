from lib import get_logger
from lib.talk.a3rt import A3RT
# from lib.talk.seq2seq import Seq2seq


class Talk:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.talk_api = A3RT()
        # self.talk_api = Seq2seq()

    def talking(self, slack, words):
        talking = ' '.join(words)
        res = ''
        try:
            res = self.talk_api.talk(talking)
            if res != '':
                message_text = res + " :nifbot:"
                slack.reply(message_text)
                self.logger.info(message_text)
                return True
            else:
                return False
        except:
            self.logger.warning("Talk APIで例外が発生しました")
            import traceback
            traceback.print_exc()
            return False
