import re
import numpy as np
from lib import get_logger
from lib.aws.s3 import S3


class CompanyMaster:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.s3 = S3()

    def search_master(self, message, master_name_text, filename, search_words, search_columns, search_column_regex, get_columns):
        self.logger.info(f"{master_name_text}検索を開始")

        # 検索対象カラムの形式のみのリストに変換
        search_words = [s for s in search_words if re.match(search_column_regex, s)]

        hit = self.search_master_ex(message, master_name_text, filename, search_columns, search_words, get_columns)
        # ヒット件数が返ってきたらそのまま返す（0件かたくさんヒットした場合なので）
        if type(hit) is int:
            return hit

        message_texts = self.get_message_text(master_name_text, hit)
        message.reply("\n".join(message_texts))

        # ヒット件数を返す
        return len(hit)

    def search_master_ex(self, message, master_name_text, filename, search_columns, search_words, get_columns):

        df = self.get_master_df(filename=filename)
        # 検索結果のndarrayを入れる変数
        hit = None

        for word in search_words:
            # 検索対象カラムで検索
            for search_column in search_columns:
                search_dict = {
                    search_column: word
                }
                target_df = self.get_target_df(df, search_dict)
                self.logger.debug(target_df)
                # 取得できなければ次へ
                if len(target_df) == 0:
                    continue
                if len(target_df) >= 200:
                    message.reply(f"{master_name_text}を検索したらたくさんヒットしちゃいました...！")
                    return len(target_df)
                # 取得できたらndarrayを取得結果(target)に追加
                values = target_df[get_columns].fillna('').values
                self.logger.debug(values)
                if hit is None:
                    hit = values
                else:
                    hit = np.concatenate([hit, values])
        self.logger.debug(hit)

        if hit is None or len(hit) == 0:
            self.logger.debug(f"{master_name_text}を検索しましたが見つかりませんでした")
            return 0

        return hit

    def get_master_df(self, filename):
        return self.s3.load_company_master(filename=filename)

    def get_target_df(self, df, search_dict):
        for column, word in search_dict.items():
            df = df[df[column].fillna('').str.contains(word, case=False)]

        return df

    def get_message_text(self, master_name_text, hit):
        message_texts = list()
        message_texts.append(f"{master_name_text}を検索しました！")
        for i in range(len(hit)):
            target_texts = list()
            for j in range(len(hit[i])):
                target_texts.append(str(hit[i, j]))
            message_texts.append(f"{' '.join(target_texts)}")
        return message_texts
