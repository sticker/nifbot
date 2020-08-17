from lib import get_logger
from lib.aws.kendra import Kendra


class Faq:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.kendra = Kendra()

    def ask(self, message, words):
        query = ' '.join(words)
        res = ''
        try:
            res = self.kendra.search(query)
            if res != '':
                message_text = res + " :nifbot:"
                message.reply(message_text)
                self.logger.info(message_text)
                return True
            else:
                return False
        except:
            self.logger.warning("Kendraで例外が発生しました")
            import traceback
            traceback.print_exc()
            return False
