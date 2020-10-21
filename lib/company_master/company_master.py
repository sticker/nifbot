import re
import numpy as np
from lib import get_logger
from lib.aws.s3 import S3


class CompanyMaster:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.s3 = S3()
        self.max_count = 110

    def search_master(self, slack, master_name_text, filename, search_words, search_columns, search_column_regex, get_columns):
        self.logger.info(f"{master_name_text}検索を開始")

        # 検索対象カラムの形式のみのリストに変換
        search_words = [s for s in search_words if re.match(search_column_regex, s)]

        hit_count, hit = self.search_master_ex(master_name_text, filename, search_columns, search_words, get_columns)
        # ヒット件数が0件ならそのまま0を返す
        if hit_count == 0:
            return hit_count

        # 検索結果から重複を削除してソート
        hit = np.array(list(map(list, set(map(tuple, hit)))))
        hit = hit[hit[:, 0].argsort(), :]

        message_texts, blocks = self.get_message_text(master_name_text, hit_count, hit)
        slack.reply("\n".join(message_texts), blocks=blocks)
        self.logger.info("\n".join(message_texts))

        # ヒット件数を返す
        return hit_count

    def search_master_ex(self, master_name_text, filename, search_columns, search_words, get_columns):

        df = self.get_master_df(filename=filename)
        # 検索結果のndarrayを入れる変数
        hit = None
        hit_count = 0

        for word in search_words:
            # 検索対象カラムで検索
            for search_column in search_columns:
                search_dict = {
                    search_column: word
                }
                target_df = self.get_target_df(df, search_dict)
                # 取得できなければ次へ
                if len(target_df) == 0:
                    continue
                # 取得できたらndarrayを取得結果(target)に追加
                values = target_df[get_columns].fillna('').values
                if hit is None:
                    hit = values
                elif len(hit) + len(values) < self.max_count:
                    hit = np.concatenate([hit, values])
                else:
                    # 返却可能な最大件数を超えているため検索終了
                    break
        self.logger.debug(hit)

        if hit is None or len(hit) == 0:
            self.logger.debug(f"{master_name_text}を検索しましたが見つかりませんでした")
            return hit_count, []

        hit_count = len(hit)
        return hit_count, hit

    def get_master_df(self, filename):
        return self.s3.load_company_master(filename=filename)

    def get_target_df(self, df, search_dict):
        for column, word in search_dict.items():
            df = df[df[column].astype(str).fillna('').str.contains(word, case=False)]

        return df

    def get_message_text(self, master_name_text, hit_count, hit):
        message_texts = list()
        if hit_count > self.max_count:
            message_texts.append(f"{master_name_text}を検索したら{hit_count}件もヒットしちゃいました...！{self.max_count}件だけお返ししますね。")
            hit = hit[:self.max_count]
        else:
            message_texts.append(f"{master_name_text}を検索しました！")

        return self.add_message_text_record(master_name_text, message_texts, hit)

    def add_message_text_record(self, master_name_text, message_texts, hit):
        # 社員マスタ検索でヒット数が5件以内であれば、顔写真を表示するためblocksを返す
        if master_name_text == '社員マスタ' and len(hit) <= 10:
            blocks = list()
            for i in range(len(hit)):
                section = self.generate_section_for_photo(hit[i])
                blocks.append(section)
            return message_texts, blocks
        # それ以外は検索結果をテキストに追記して返す
        for i in range(len(hit)):
            target_texts = list()
            for j in range(len(hit[i])):
                target_texts.append(str(hit[i, j]))
            message_texts.append(f"{' '.join(target_texts)}")
        return message_texts, None

    def generate_section_for_photo(self, hit_record):
        uid = hit_record[0]
        texts = list()
        # ヒットしたレコードの要素を一旦listに格納
        for j in range(len(hit_record)):
            texts.append(str(hit_record[j]))

        section = dict()
        section["type"] = "section"
        section["text"] = {
            "type": "mrkdwn",
            "text": ' '.join(texts)
        }

        # 顔写真の署名付きURLを取得
        image_url = self.s3.generate_user_photo_presigned_url(uid)
        self.logger.debug(image_url)
        # 署名付きURLを取得できればセクションに追加
        if image_url:
            section["accessory"] = {
                "type": "image",
                "image_url": image_url,
                "alt_text": uid
            }

        return section
