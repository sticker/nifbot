import pandas as pd
from lib.nifbot.company_master import CompanyMaster


class CompanyUser(CompanyMaster):
    def __init__(self):
        super().__init__()

    def search(self, message, words):
        get_columns = ['uid', 'full_name_kanji', 'mail', 'telephone_number', 'group_name', 'position_name']
        search_columns = get_columns
        hit_count = super().search_master(message, master_name_text='社員マスタ',
                                          filename=None,
                                          search_words=words,
                                          search_columns=search_columns,
                                          search_column_regex='.*',
                                          get_columns=get_columns)
        return hit_count

    def get_master_df(self, filename):
        # 結合
        df_user = self.s3.load_company_master(filename="format/user/nifty_general_user2.csv")
        df_group = self.s3.load_company_master(filename="format/group/nifty_general_org.csv")
        df_position = self.s3.load_company_master(filename="format/position/nifty_general_title.csv")
        df_user_group = pd.merge(df_user, df_group, left_on='department', right_on='group_id', how='left')
        df = pd.merge(df_user_group, df_position, left_on='position', right_on='position_id', how='left')
        return df
