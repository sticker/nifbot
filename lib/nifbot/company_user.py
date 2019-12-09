import numpy as np
import pandas as pd
from lib import get_logger
from lib.aws.s3 import S3


class CompanyUser:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.s3 = S3()

    def search(self, message, words):
        self.logger.info("社員マスタ検索を開始")
        df_user = self.s3.load_company_master(filename="format/user/nifty_general_user2.csv")
        df_group = self.s3.load_company_master(filename="format/group/nifty_general_org.csv")
        df_position = self.s3.load_company_master(filename="format/position/nifty_general_title.csv")
        df_user_group = pd.merge(df_user, df_group, left_on='department', right_on='group_id', how='left')
        df = pd.merge(df_user_group, df_position, left_on='position', right_on='position_id', how='left')
        self.logger.debug(df)

        # 検索結果のndarrayを入れる変数
        hit = None
        # 取得対象カラム
        get_columns = ['uid', 'full_name_kanji', 'mail', 'telephone_number', 'group_name', 'position_name']
        # 検索対象カラム
        search_columns = get_columns

        for word in words:
            for column in search_columns:
                # 検索対象カラムを順番に検索していく
                target_df = df[df[column].fillna('').str.contains(word, case=False)]
                self.logger.debug(target_df)
                # 取得できなければ次の検索対象カラムへ
                if len(target_df) == 0:
                    continue
                if len(target_df) >= 20:
                    message.reply("社員マスタを検索したらたくさんヒットしちゃいました...！")
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
            self.logger.debug("社員マスタを検索しましたが見つかりませんでした")
            # message.reply("社員マスタを検索しましたが見つかりませんでした...")
            return 0

        message_texts = list()
        message_texts.append("社員マスタを検索しました！")
        for i in range(len(hit)):
            target_texts = list()
            for j in range(len(hit[i])):
                target_texts.append(str(hit[i, j]))
            message_texts.append(f"{' '.join(target_texts)}")
        message.reply("\n".join(message_texts))
        return len(hit)
