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
        usages.append(f"`@{botname} [社員ID/氏名/メアド/内線/所属/役職/タグ]` : 統合アカウントを検索します")
        usages.append(f"`@{botname} [組織コード/名称]` : 組織コード/名称を検索します")
        usages.append(f"`@{botname} [プロダクトコード￿￿/￿名称]` : プロダクトコード/名称を検索します")
        usages.append(f"`@{botname} [課金大小区分(7桁数字)/名称]` : 課金大小区分/名称を検索します")
        usages.append(f"`@{botname} tag [タグ] [統合アカウント]` : 統合アカウントにタグをつけます")
        usages.append(f"`@{botname} tag [タグ]` : 指定のタグがついている統合アカウントを検索します")
        usages.append(f"`@{botname} tag [統合アカウント]` : 指定の統合アカウントについているタグを検索します")
        usages.append(f"`@{botname} tag rm [タグ] [統合アカウント]` : 統合アカウントからタグを削除します")
        # usages.append(self.get_akashi_token_body())
        # usages.append(f"`@{botname} 出勤` : AKASHIの出勤打刻をします")
        # usages.append(f"`@{botname} 退勤` : AKASHIの退勤打刻をします")
        usages.append(f"詳細は<https://atlassian.nifty.com/confluence/pages/viewpage.action?pageId=111254072|こちら>を参照してください。")
        message.send("\n".join(usages))
