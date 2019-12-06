import os
import pandas as pd
from lib import get_logger, app_home


class CompanyUser:
    def __init__(self):
        self.logger = get_logger(__name__)

    def search(self, message, words):

        message.reply("検索します！")

        df = self.load_master_company_user()
        self.logger.debug(df)
        target_df = df[df['uid'].str.contains(words[0], case=False)]
        self.logger.debug(target_df)
        target = target_df.values
        self.logger.debug(target)

        message_texts = list()
        message_texts.append("検索しました！")
        message_texts.append(f"{target[0, 0]} {target[0, 1]}")
        message.reply("\n".join(message_texts))


    def load_master_company_user(self, filename="company_user.csv"):
        target = os.path.join(app_home, 'lib', 'nifbot', filename)
        df = pd.read_csv(target)
        return df
