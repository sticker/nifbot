import re
import pandas as pd
from lib.nifbot.company_master import CompanyMaster


class CompanyCommodity(CompanyMaster):
    def __init__(self):
        super().__init__()
        self.master_name_text = '商品マスタ'
        self.filename = 'format/commodity/commodity-code.csv'
        self.get_columns = ['charge_code', 'commodity_kanji_name', 'charge_sec_code', 'group_name']

    def get_master_df(self, filename):
        # 結合
        df_commodity = self.s3.load_company_master(filename="format/commodity/commodity-code.csv")
        df_group = self.s3.load_company_master(filename="format/group/nifty_general_org.csv")
        df = pd.merge(df_commodity, df_group, left_on='charge_sec_code', right_on='group_id', how='left')
        # 課金大区分・小区分から課金コードの列を作る
        df['charge_code'] = df['large_kbn'].astype(str).str.zfill(2) + df['details_kbn'].astype(str).str.zfill(5)
        return df

    def search_by_charge_code(self, message, words):
        charge_code_regex = '[0-9]{7}'
        charge_codes = [s for s in words if re.match(charge_code_regex, s)]
        if len(charge_codes) > 0:
            hit_count = super().search_master(message, master_name_text=self.master_name_text,
                                              filename=self.filename,
                                              search_words=charge_codes,
                                              search_columns=['charge_code'],
                                              search_column_regex=charge_code_regex,
                                              get_columns=self.get_columns)
            return hit_count

        return 0

    def search_by_name(self, message, words):
        hit_count = super().search_master(message, master_name_text=self.master_name_text,
                                          filename=self.filename,
                                          search_words=words,
                                          search_columns=['commodity_kanji_name'],
                                          search_column_regex='.*',
                                          get_columns=self.get_columns)
        return hit_count
