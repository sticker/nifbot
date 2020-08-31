import re
from lib.company_master.company_master import CompanyMaster


class CompanyProduct(CompanyMaster):
    def __init__(self):
        super().__init__()
        self.master_name_text = 'プロダクトコードマスタ'
        self.filename = 'format/product/ProductCodeMaster.csv'
        self.get_columns = ['product_code', 'product_name', 'owner_devision', 'owner_department']

    def search_by_code(self, slack, words):
        product_code_regex = '[a-zA-Z][0-9]{4}'
        product_codes = [s for s in words if re.match(product_code_regex, s)]
        if len(product_codes) > 0:
            # プロダクトマスタを検索
            hit_count = super().search_master(slack, master_name_text=self.master_name_text,
                                              filename=self.filename,
                                              search_words=product_codes,
                                              search_columns=['product_code'],
                                              search_column_regex=product_code_regex,
                                              get_columns=self.get_columns)
            return hit_count

        return 0

    def search_by_name(self, slack, words):
        hit_count = super().search_master(slack, master_name_text=self.master_name_text,
                                          filename=self.filename,
                                          search_words=words,
                                          search_columns=['product_name'],
                                          search_column_regex='.*',
                                          get_columns=self.get_columns)
        return hit_count
