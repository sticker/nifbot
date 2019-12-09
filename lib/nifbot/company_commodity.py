import re
import numpy as np
from lib import get_logger
from lib.aws.s3 import S3


class CompanyCommodity:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.s3 = S3()

    def search(self, message, words):
        self.logger.info("商品マスタ検索を開始")
        df = self.s3.load_company_master(filename="format/commodity/commodity-code.csv")

        # 7桁数字のみのリストに変換
        words = [s for s in words if re.match('[0-9]{7}', s)]

        # 検索結果のndarrayを入れる変数
        hit = None
        # 取得対象カラム
        get_columns = ['commodity_kanji_name', 'large_kbn', 'details_kbn']

        for word in words:
            large_kbn = int(word[0:2])
            details_kbn = int(word[3:7])
            self.logger.debug(f"large_kbn={large_kbn} details_kbn={details_kbn}")
            self.logger.debug(df['large_kbn'])
            self.logger.debug(df['details_kbn'])
            # 課金大小区分で検索
            target_df = df[(df['large_kbn'] == large_kbn) & (df['details_kbn'] == details_kbn)]
            self.logger.debug(target_df)
            # 取得できなければ次へ
            if len(target_df) == 0:
                continue
            if len(target_df) >= 20:
                message.reply("商品マスタを検索したらたくさんヒットしちゃいました...！")
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
            self.logger.debug("課金コードを検索しましたが見つかりませんでした")
            # message.reply("課金コードを検索しましたが見つかりませんでした...")
            return 0

        message_texts = list()
        message_texts.append("商品マスタを検索しました！")
        for i in range(len(hit)):
            charge_code = str(hit[i, 1]).zfill(2) + str(hit[i, 2]).zfill(5)
            message_texts.append(f"{charge_code} {str(hit[i, 0])}")
        message.reply("\n".join(message_texts))
        return len(hit)
