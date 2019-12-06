from lib import get_logger


class Help:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.botname = "nifbot"

    def default(self, message):
        botname = self.botname

        usages = list()
        usages.append(f"`@{botname} [社員ID/社員氏名]` : 指定したID/氏名の社員を検索します")

        message.send("\n".join(usages))
