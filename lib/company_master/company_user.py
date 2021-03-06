import re
import pandas as pd
import numpy as np
from lib.company_master.company_master import CompanyMaster
from lib.company_master.company_user_tag import CompanyUserTag


class CompanyUser(CompanyMaster):
    def __init__(self):
        super().__init__()
        self.company_user_tag = CompanyUserTag()

    def search(self, slack, words):
        get_columns = ['uid', 'full_name_kanji', 'mail', 'telephone_number', 'group_id', 'group_name', 'position_name']
        search_columns = get_columns
        hit_count = self.search_master(slack, master_name_text='社員マスタ',
                                       filename=None,
                                       search_words=words,
                                       search_columns=search_columns,
                                       search_column_regex='.*',
                                       get_columns=get_columns)
        return hit_count

    def search_master(self, slack, master_name_text, filename, search_words, search_columns, search_column_regex, get_columns):
        self.logger.info(f"{master_name_text}検索を開始")

        # 検索対象カラムの形式のみのリストに変換
        search_words = [s for s in search_words if re.match(search_column_regex, s)]
        # マスタ検索
        hit_count, hit = self.search_master_ex(master_name_text, filename, search_columns, search_words, get_columns)

        # タグあいまい検索
        uids = self.company_user_tag.get_uids_by_tags(search_words)
        # 正式なタグ名とIDの辞書リストが返ってくるので、IDのみのリストを作る
        tag_uids = list()
        for uid in uids:
            tag_uids.append(uid['uid'])
        # タグ検索でヒットしたら、そのIDでマスタ検索して結果に追加する
        if len(tag_uids) > 0:
            # マスタ検索
            hit_count_tag, hit_tag = self.search_master_ex(master_name_text, filename, ['uid'], tag_uids, get_columns)
            hit_count += hit_count_tag
            if len(hit) == 0:
                hit = hit_tag
            else:
                hit = np.concatenate([hit, hit_tag])

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

    def get_master_df(self, filename):
        # 結合
        df_user = self.s3.load_company_master(filename="format/user/nifty_general_user.csv")
        df_group = self.s3.load_company_master(filename="format/group/nifty_general_org.csv")
        df_position = self.s3.load_company_master(filename="format/position/nifty_general_title.csv")
        df_user_group = pd.merge(df_user, df_group, left_on='department', right_on='group_id', how='left')
        df = pd.merge(df_user_group, df_position, left_on='position', right_on='position_id', how='left')
        return df
