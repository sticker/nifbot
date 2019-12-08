from lib import get_logger, app_home
from logging import DEBUG
from boto3 import Session
from datetime import datetime
import os
import pandas as pd


class S3(object):
    S3_BUCKET_COMPANY_MASTER = "company-master"

    def __init__(self):
        self.logger = get_logger(__name__)
        region_name = os.getenv('AWS_REGION', 'ap-northeast-1')
        # 環境変数 AWS_REGION が設定されていない場合は処理しない
        if region_name != '':
            session = Session(region_name=region_name)
            self.resource = session.resource('s3')

    def upload(self, bucket_name: str, path_local: str, path_s3: str):
        self.logger.log(DEBUG, f"upload: bucket_name={bucket_name} path_s3={path_s3} path_local={path_local}")
        self.resource.Bucket(bucket_name).upload_file(path_local, path_s3)

    def download(self, bucket_name: str, path_s3: str, path_local: str):
        self.logger.log(DEBUG, f"download: bucket_name={bucket_name} path_s3={path_s3} path_local={path_local}")
        self.resource.Bucket(bucket_name).download_file(path_s3, path_local)

    def download_company_master(self, key: str, path_local: str):
        self.download(self.S3_BUCKET_COMPANY_MASTER, key, path_local)

    def load_company_master(self, filename):
        # マスタファイルのローカル保存名（フルパス）
        local_path = os.path.join(app_home, filename)

        if not os.path.exists(local_path):
            # ローカルにファイルがなければS3からダウンロード
            self.download_company_master(filename, local_path)
        else:
            # ローカルにファイルが有れば、更新日時を取得
            last_download_time = datetime.fromtimestamp(os.path.getmtime(local_path))
            self.logger.debug(last_download_time)
            # 更新日時が今日の0時以前であればS3からダウンロード
            today_midnight = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            self.logger.debug(today_midnight)

            if last_download_time < today_midnight:
                self.download_company_master(filename, local_path)

        df = pd.read_csv(local_path)
        return df
