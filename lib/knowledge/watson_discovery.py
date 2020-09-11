import os
import json
import re
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from ibm_watson import DiscoveryV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from lib import get_logger, app_home


class WatsonDiscovery:
    def __init__(self):
        self.logger = get_logger(__name__)
        # for IBM Watson Discovery
        apikey = os.getenv('WATSON_DISCOVERY_API_KEY', 'zfLyg6DnAvMy7oDGMzOMj1LlJf9tDpo1SWwbb0inLYUE')
        version = os.getenv('WATSON_DISCOVERY_API_VERSION', '2019-04-30')
        url = os.getenv('WATSON_DISCOVERY_SERVICE_URL',
                        'https://api.jp-tok.discovery.watson.cloud.ibm.com/instances/cba9436a-8e1c-412e-a2c1-36eaaedcbb87')
        authenticator = IAMAuthenticator(f'{apikey}')
        self.discovery = DiscoveryV1(
            version=f'{version}',
            authenticator=authenticator
        )
        self.discovery.set_service_url(f'{url}')
        self.environment_id = os.getenv('WATSON_DISCOVERY_ENVIRONMENT_ID', '6155a670-d884-43aa-afd7-4d7c5880e3d1')
        self.collection_id = os.getenv('WATSON_DISCOVERY_COLLECTION_ID', 'd68786dd-10e7-4bf0-86fe-b840b434bd2c')
        # 返答としてpassageを採用するscoreのしきい値
        self.passage_score_threshold = 20

        # for IBM Cloud Object Storage
        # Constants for IBM COS values
        COS_ENDPOINT = os.getenv('COS_ENDPOINT', "https://s3.jp-tok.cloud-object-storage.appdomain.cloud")
        COS_API_KEY_ID = os.getenv('COS_API_KEY_ID', "lrbBmMu1tBkWoxqt3ZvxrGmkRQMgaKa5eZp5LYyjVaoS")
        COS_AUTH_ENDPOINT = os.getenv('COS_AUTH_ENDPOINT', "https://iam.cloud.ibm.com/identity/token")
        COS_RESOURCE_CRN = os.getenv('COS_RESOURCE_CRN',
                                     "crn:v1:bluemix:public:cloud-object-storage:global:a/1dc861249cb942efabf32f603d9b7671:c1a38fe9-ff82-487e-b4f5-05caeec8338a::")
        # Create resource
        self.cos = ibm_boto3.resource("s3",
                                      ibm_api_key_id=COS_API_KEY_ID,
                                      ibm_service_instance_id=COS_RESOURCE_CRN,
                                      ibm_auth_endpoint=COS_AUTH_ENDPOINT,
                                      config=Config(signature_version="oauth"),
                                      endpoint_url=COS_ENDPOINT
                                      )

    def query(self, query):
        try:
            res = self.discovery.query(environment_id=self.environment_id, collection_id=self.collection_id,
                                       natural_language_query=query, passages=True, highlight=True, count=5,
                                       passages_count=1, passages_characters=100)

            # 返答するblocks
            blocks = list()

            # クエリが失敗した場合は処理終了
            if res.get_status_code() != 200:
                blocks.append(self.make_error_section())
                return blocks, None

            # 信頼度の高いpassageがヒットしたかどうか
            passage_hit = False

            # まずpassageのスコアがしきい値以上なら passage_text を返す
            result_all = res.get_result()
            passage = result_all['passages'][0]
            passage_score = passage['passage_score']
            if passage_score >= self.passage_score_threshold:
                passage_text = passage['passage_text']
                field = passage['field']
                # htmlならタグを削除する
                if field == 'html':
                    passage_text = self.delete_html_tag(passage_text)

                hit_message = f"答えが見つかったよ！\n```{passage_text}```\n"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": hit_message
                    }
                })
                passage_hit = True

            # resultsを取得
            results = result_all['results']
            # resultsが無ければ処理終了
            if len(results) == 0:
                return blocks, None
            # resultsがあれば結果をフィードバックしてもらう
            feedback_message = "関係ありそうなページが見つかったよ。フィードバックして教えてね。"
            if passage_hit:
                feedback_message = "他にも" + feedback_message
            blocks.append({
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": feedback_message,
                    "emoji": True
                }
            })

            attachments = list()
            for result in results:
                document_id = result['id']
                # COSオブジェクトのメタデータからページURLを取得
                bucket_name = result['metadata']['source']['Name']
                item_name = result['metadata']['source']['Key']
                file = self.cos.Object(bucket_name, item_name).get()
                page_url = file['Metadata'].get('page_url')
                # item_nameの先頭にConfluenceのスペースキーがあるので取り除く
                page_title = '/'.join(item_name.split('/')[1:])
                highlight_text = result['highlight']['text'][0]
                # タグを削除
                highlight_text = self.delete_html_tag(highlight_text)
                # blocksに「関係ありそうなページ」部分を追加
                attachments.append({"blocks": self.make_results_section(page_title, page_url, highlight_text, query, document_id)})

            return blocks, attachments
        except Exception:
            self.logger.warning("Watson Discoveryで例外が発生しました")
            import traceback
            traceback.print_exc()
            return [self.make_error_section()], None

    def delete_html_tag(self, str):
        """
        strに含まれるHTMLタグを削除して返す
        :param str:
        :return:
        """
        del_html_tag = re.compile(r"<[^>]*?>")
        return del_html_tag.sub("", str)

    def make_error_section(self):
        """
        エラー発生時のメッセージセクションを返す
        :return: dict エラーメッセージのセクション
        """
        section = {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "すいません、調子が悪いみたいです。。:scream:",
                "emoji": True
            }
        }
        return section

    def make_results_section(self, page_title: str, page_url: str, highlight_text: str, query: str, document_id: str):
        """
        「関係ありそうなページ」の部分を作る
        :param page_title: 文書のページタイトル
        :param page_url: 文書のページURL
        :param highlight_text: 文書のhighlightテキスト
        :param query: クエリテキスト
        :param document_id: 文書のID
        :return: list 「関係ありそうなページ」部分のlist
        """
        blocks = list()
        divider = {
            "type": "divider"
        }
        blocks.append(divider)

        section = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<{page_url}|{page_title}>```{highlight_text}```"
            }
        }
        blocks.append(section)

        action = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "nifbot_knowledge_feedback_ok",
                    "text": {
                        "type": "plain_text",
                        "text": ":+1: これ！",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": f"{query}__{document_id}"
                },
                {
                    "type": "button",
                    "action_id": "nifbot_knowledge_feedback_ng",
                    "text": {
                        "type": "plain_text",
                        "text": ":persevere: 関係ない",
                        "emoji": True
                    },
                    "style": "danger",
                    "value": f"{query}__{document_id}"
                }
            ]
        }
        blocks.append(action)

        return blocks
