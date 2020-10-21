from lib import get_logger, app_home
from logging import DEBUG
from boto3 import Session
from datetime import datetime
import os
import pandas as pd


class S3(object):
    S3_BUCKET_COMPANY_MASTER = "nifty-master-data-518017743882-ap-northeast-1"

    def __init__(self):
        self.logger = get_logger(__name__)
        self.region_name = os.getenv('AWS_REGION', 'ap-northeast-1')
        # 環境変数 AWS_REGION が設定されていない場合は処理しない
        if self.region_name != '':
            self.session = Session(region_name=self.region_name)
            self.resource = self.session.resource('s3')
            self.company_master_resource = None
            self.company_master_client = None

    def get_session_assume_role(self):
        company_master_sts = self.session.client("sts")
        self.logger.info(f"セッションを取得しました。ロールArn：{company_master_sts.get_caller_identity()['Arn']}")

        cred = company_master_sts.assume_role(
            RoleArn='arn:aws:iam::518017743882:role/MasterDataS3AccessRole',
            RoleSessionName=f"company-master-role-session"
        )
        company_master_session = Session(
            aws_access_key_id=cred["Credentials"]['AccessKeyId'],
            aws_secret_access_key=cred["Credentials"]['SecretAccessKey'],
            aws_session_token=cred["Credentials"]['SessionToken'],
            region_name=self.region_name
        )
        return company_master_session

    def set_company_master_resource(self):
        company_master_session = self.get_session_assume_role()
        self.company_master_resource = company_master_session.resource('s3')

    def set_company_master_client(self):
        company_master_session = self.get_session_assume_role()
        self.company_master_client = company_master_session.client('s3')

    def upload(self, resource, bucket_name: str, path_local: str, path_s3: str):
        self.logger.log(DEBUG, f"upload: bucket_name={bucket_name} path_s3={path_s3} path_local={path_local}")
        resource.Bucket(bucket_name).upload_file(path_local, path_s3)

    def download(self, resource, bucket_name: str, path_s3: str, path_local: str):
        self.logger.log(DEBUG, f"download: bucket_name={bucket_name} path_s3={path_s3} path_local={path_local}")
        resource.Bucket(bucket_name).download_file(path_s3, path_local)

    def download_company_master(self, key: str, path_local: str):
        self.set_company_master_resource()
        self.download(self.company_master_resource, self.S3_BUCKET_COMPANY_MASTER, key, path_local)

    def load_company_master(self, filename):
        # マスタファイルのローカル保存名（フルパス）
        local_path = os.path.join(app_home, os.path.basename(filename))

        if not os.path.exists(local_path):
            # ローカルにファイルがなければS3からダウンロード
            self.download_company_master(filename, local_path)
        else:
            # ローカルにファイルが有れば、更新日時を取得
            last_download_time = datetime.fromtimestamp(os.path.getmtime(local_path))
            # 更新日時が今日の0時以前であればS3からダウンロード
            today_midnight = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

            if last_download_time < today_midnight:
                self.download_company_master(filename, local_path)

        df = pd.read_csv(local_path)
        return df

    def generate_user_photo_presigned_url(self, uid: str, expires_in=300):
        try:
            if self.company_master_client is None:
                self.set_company_master_client()

            bucket_name = self.S3_BUCKET_COMPANY_MASTER
            key = f"format/user_photo/{uid.upper()}.jpg"
            # key = f"original/user_photo/{uid.upper()}.jpg"

            # ファイルの存在確認　ファイルがなければClientErrorの例外発生
            self.company_master_client.get_object(
                Bucket=bucket_name,
                Key=key
            )
            # ファイルが存在すれば署名付きURLを取得
            presigned_url = self.company_master_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=expires_in,
                HttpMethod='GET')
            return presigned_url
        except:
            self.logger.info(f"署名付きURLの取得に失敗しました uid={uid}")
            import traceback
            traceback.print_exc()
            return ""
