import re
from lib.company_master.company_master import CompanyMaster


class CompanyGroup(CompanyMaster):
    def __init__(self):
        super().__init__()
        self.master_name_text = '組織マスタ'
        self.filename = 'format/group/nifty_general_org.csv'
        self.get_columns = ['group_id', 'group_name']

    def search_by_code(self, slack, words):
        group_id_regex = '[a-zA-Z][0-9]{3}'
        group_ids = [s for s in words if re.match(group_id_regex, s)]
        if len(group_ids) > 0:
            # 組織マスタを検索
            hit_count = super().search_master(slack, master_name_text=self.master_name_text,
                                              filename=self.filename,
                                              search_words=group_ids,
                                              search_columns=['group_id'],
                                              search_column_regex=group_id_regex,
                                              get_columns=self.get_columns)
            return hit_count

        return 0

    def search_by_name(self, slack, words):
        hit_count = super().search_master(slack, master_name_text=self.master_name_text,
                                          filename=self.filename,
                                          search_words=words,
                                          search_columns=['group_name'],
                                          search_column_regex='.*',
                                          get_columns=self.get_columns)
        return hit_count
