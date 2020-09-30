from lib import get_logger, app_home
import boto3
import os
import re
import pprint
from boto3 import Session
from lib.aws.translate import Translate


class Kendra(object):

    def __init__(self):
        self.logger = get_logger(__name__)
        # Kendraは東京リージョン対応していないため、バージニア北部リージョンを使う
        region_name = os.getenv('AWS_REGION_KENDRA', 'us-east-1')
        session = Session(region_name=region_name)
        self.client = session.client('kendra')
        # 処理対象のKendraインデックスID
        self.kendra_index_id = os.getenv('KENDRA_INDEX_ID', 'aa69a4f0-6a1e-401f-a04b-8f8dbf7f7476')
        # Translate
        self.translate = Translate()
        # KendraのデータソースとしてのS3はKendraと同じリージョンである必要があるので同じセッションで扱う
        self.s3 = session.resource('s3')

    def search(self, query):
        """
        検索文（日本語）をKendra（英語）で検索し、検索結果を日本語翻訳し応答文として整形して返す
        :param query: 検索文（日本語）
        :return: 応答文（日本語）
        """
        # 検索文を英語に翻訳
        query = self.translate.translate_text(text=query, source_lang='ja', target_lang='en')
        # Find the most relevant document.
        response = self.client.query(IndexId=self.kendra_index_id, QueryText=query)
        pprint.pprint(response)
        # Create response message.
        message = ''
        # 検索結果3件を取得し、返却メッセージに含める
        for i, item in enumerate(response['ResultItems'][:3]):
            print(item)
            title_en = item['DocumentTitle']['Text']
            if title_en is not None and title_en != "":
                # ドキュメントタイトルがあれば日本語翻訳する
                title = self.translate.translate_text(text=title_en, source_lang='en', target_lang='ja')
            else:
                title = title_en

            excerpt_en = item['DocumentExcerpt']['Text']
            # 検索結果文（抜粋）を日本語翻訳する
            excerpt = self.translate.translate_text(text=excerpt_en, source_lang='en', target_lang='ja')
            # 複数の改行があれば一つにまとめる
            excerpt = re.sub(r"\n+", "\n", excerpt)

            # S3にあるドキュメントのメタデータに設定されている、「ドキュメントのURL情報」を取得する
            # TODO: FAQにヒットした場合はS3ドキュメントはない
            s3_uri = item['DocumentId'].replace('s3://', '').split('/')
            url = self.s3.Object(s3_uri[0], '/'.join(s3_uri[1:])).metadata['url']

            # 返却するメッセージに追記する
            message_i = f'{i + 1}. *{title}*{os.linesep}url: {url}{os.linesep}```{excerpt}```{os.linesep}{os.linesep}'
            #message_i = f'{i + 1}. *title:{title}*{os.linesep}```{excerpt}```{os.linesep}{os.linesep}'
            message += message_i
        return message
