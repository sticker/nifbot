from lib import get_logger
from boto3 import Session
import os


class Translate(object):
    def __init__(self):
        self.logger = get_logger(__name__)
        region_name = os.getenv('AWS_REGION', 'ap-northeast-1')
        session = Session(region_name=region_name)
        self.client = session.client('translate')

    def translate_text(self, text: str, source_lang: str, target_lang: str):
        """
        テキストを翻訳して結果を返す
        :param text: 翻訳対象のテキスト
        :param source_lang: 翻訳前の言語コード（'en', 'ja',,,）
        :param target_lang: 翻訳後の言語コード（'en', 'ja',,,）
        :return: 翻訳後のテキスト
        """
        response = self.client.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        translated_text = response['TranslatedText']
        return translated_text
