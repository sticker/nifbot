import re
import pandas as pd
from lib.nifbot.company_master import CompanyMaster


class CompanyCommodity(CompanyMaster):
    def __init__(self):
        super().__init__()
        self.master_name_text = '商品マスタ'
        self.filename = 'format/commodity/commodity-code.csv'
        self.get_columns = ['commodity_kanji_name', 'large_kbn', 'details_kbn', 'charge_sec_code', 'group_name']

    def get_master_df(self, filename):
        # 結合
        df_commodity = self.s3.load_company_master(filename="format/commodity/commodity-code.csv")
        df_group = self.s3.load_company_master(filename="format/group/nifty_general_org.csv")
        df = pd.merge(df_commodity, df_group, left_on='charge_sec_code', right_on='group_id', how='left')
        return df

    def search_by_charge_code(self, message, words):
        charge_code_regex = '[0-9]{7}'
        charge_codes = [s for s in words if re.match(charge_code_regex, s)]
        if len(charge_codes) > 0:
            hit_count = super().search_master(message, master_name_text=self.master_name_text,
                                              filename=self.filename,
                                              search_words=charge_codes,
                                              # charge_codeというカラムは無いが、課金大区分/小区分のAND条件で検索される
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

    def get_target_df(self, df, search_dict):
        search_column = list(search_dict.keys())[0]
        self.logger.debug(search_column)
        if search_column == 'charge_code':
            charge_code = list(search_dict.values())[0]
            large_kbn = int(charge_code[0:2])
            details_kbn = int(charge_code[3:7])
            df = df[(df['large_kbn'] == large_kbn) & (df['details_kbn'] == details_kbn)]
        else:
            for column, word in search_dict.items():
                df = df[df[column].fillna('').str.contains(word, case=False)]

        return df

    def add_message_text_record(self, message_texts, hit):
        for i in range(len(hit)):
            charge_code = str(hit[i, 1]).zfill(2) + str(hit[i, 2]).zfill(5)
            message_texts.append(f"{charge_code} {str(hit[i, 0])} {str(hit[i, 3])}:{str(hit[i, 4])}")
        return message_texts
