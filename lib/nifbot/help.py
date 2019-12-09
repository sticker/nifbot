from lib import get_logger


class Help:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.botname = "nifbot"

    def get_akashi_token_body(self):
        botname = self.botname
        return f"`@{botname} token [AKASHI APIトークン]` : AKASHIのAPIトークンを設定します"

    def akashi_token(self, message):
        usages = list()
        usages.append(self.get_akashi_token_body())
        message.send("\n".join(usages))

    def default(self, message):
        botname = self.botname

        usages = list()
        usages.append(f"`@{botname} [社員ID/社員氏名]` : 指定したID/氏名の社員を検索します")
        usages.append(f"`@{botname} [課金コード￿(大小区分 7桁数字)]` : 商品を検索します")
        usages.append(self.get_akashi_token_body())
        usages.append(f"`@{botname} 出勤` : AKASHIの出勤打刻をします")
        usages.append(f"`@{botname} 退勤` : AKASHIの退勤打刻をします")
        message.send("\n".join(usages))
