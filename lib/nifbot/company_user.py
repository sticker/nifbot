import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from lib import get_logger, app_home
from lib.aws.s3 import S3


class CompanyUser:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.s3 = S3()

    def search(self, message, words):
        df = self.load_master_company_user()

        # 検索結果のndarrayを入れる変数
        hit = None
        # 取得対象カラム
        get_columns = ['uid', 'full_name_kanji', 'mail', 'telephone_number']
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
                    message.reply("たくさんヒットしちゃったのでもう少し絞り込んでください...！")
                    return
                # 取得できたらndarrayを取得結果(target)に追加
                values = target_df[get_columns].fillna('').values
                self.logger.debug(values)
                if hit is None:
                    hit = values
                else:
                    hit = np.concatenate([hit, values])
        self.logger.debug(hit)

        if hit is None or len(hit) == 0:
            message.reply("見つかりませんでした...")
            return

        message_texts = list()
        message_texts.append("見つかりましたよ！")
        for i in range(len(hit)):
            target_texts = list()
            for j in range(len(hit[i])):
                target_texts.append(str(hit[i, j]))
            message_texts.append(f"{' '.join(target_texts)}")
        message.reply("\n".join(message_texts))

    def load_master_company_user(self, filename="company_user.csv"):
        # マスタファイルのローカル保存名（フルパス）
        local_path = os.path.join(app_home, 'lib', 'nifbot', filename)

        if not os.path.exists(local_path):
            # ローカルにファイルがなければS3からダウンロード
            self.s3.download_company_master(filename, local_path)
        else:
            # ローカルにファイルが有れば、更新日時を取得
            last_download_time = datetime.fromtimestamp(os.path.getmtime(local_path))
            self.logger.debug(last_download_time)
            # 更新日時が昨日以前であればS3からダウンロード
            yesterday = datetime.today() - timedelta(days=1)
            self.logger.debug(yesterday)
            if last_download_time < yesterday:
                self.s3.download_company_master(filename, local_path)

        df = pd.read_csv(local_path)
        return df
