import re
import config
from ibm_cloud_sdk_core import ApiException
from lib import get_logger


class WatsonDiscovery:
    def __init__(self):
        self.logger = get_logger(__name__)

    def query(self, query):
        res = config.watson_discovery.query(environment_id=config.environment_id,
                                            collection_id=config.collection_id,
                                            natural_language_query=query,
                                            passages=True,
                                            highlight=True,
                                            count=config.results_count,
                                            passages_count=config.passages_count,
                                            passages_characters=config.passages_characters)
        # 返答するblocks
        blocks = list()

        # クエリが失敗した場合は処理終了
        if res.get_status_code() != 200:
            return None, None

        # 信頼度の高いpassageがヒットしたかどうか
        passage_hit = False
        # まずpassageのスコアがしきい値以上なら passage_text を返す
        result_all = res.get_result()
        passage = result_all['passages'][0]
        passage_score = passage['passage_score']
        if passage_score >= config.passage_score_threshold:
            passage_text = passage['passage_text']
            field = passage['field']
            # htmlならタグを削除する
            if field == 'html':
                passage_text = self.delete_html_tag(passage_text)
            hit_message = f"こんな記載が見つかったよ！\n```{passage_text}```\n"
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

        # フィードバック用にクエリを登録し、query_idを取得しておく
        query_id = self.add_training_data(query)
        attachments = list()
        for result in results:
            document_id = result['id']
            page_url = result.get('page_url')
            page_title = result.get('title')
            if page_url is None:
                # COSオブジェクトのメタデータからページURLを取得
                bucket_name = result['metadata']['source']['Name']
                item_name = result['metadata']['source']['Key']
                file = config.cos.Object(bucket_name, item_name).get()
                page_url = file['Metadata'].get('page_url')
                # item_nameの先頭にConfluenceのスペースキーがあるので取り除く
                page_title = '/'.join(item_name.split('/')[1:])
            if result['highlight'].get('text') is not None:
                highlight = result['highlight']['text'][0]
            elif result['highlight'].get('html') is not None:
                highlight = result['highlight']['html'][0]
            else:
                highlight = ""
            # タグを削除
            highlight_text = self.delete_html_tag(highlight)
            # blocksに「関係ありそうなページ」部分を追加
            attachments.append({"blocks": self.make_results_section(page_title, page_url, highlight_text, query, query_id, document_id)})

        return blocks, attachments

    def delete_html_tag(self, str):
        """
        strに含まれるHTMLタグを削除して返す
        :param str:
        :return:
        """
        del_html_tag = re.compile(r"<[^>]*?>")
        return del_html_tag.sub("", str)

    def make_results_section(self, page_title: str, page_url: str, highlight_text: str, query: str, query_id: str, document_id: str):
        """
        「関係ありそうなページ」の部分を作る
        :param page_title: 文書のページタイトル
        :param page_url: 文書のページURL
        :param highlight_text: 文書のhighlightテキスト
        :param query: クエリテキスト
        :param query_id: トレーニング用に登録したクエリID
        :param document_id: 文書のID
        :return: list 「関係ありそうなページ」部分のlist
        """
        blocks = list()
        divider = {
            "type": "divider"
        }
        blocks.append(divider)

        highlight = highlight_text
        if len(highlight_text) > 0:
            highlight = f"```{highlight_text}```"
        section = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<{page_url}|{page_title}>{highlight}"
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
                    "value": f"{query_id}__{document_id}"
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
                    "value": f"{query_id}__{document_id}"
                }
            ]
        }
        blocks.append(action)

        return blocks

    def add_training_data(self, query, filter=None, examples=None):
        """
        Discoveryのadd_training_dataメソッドを実行する
        :param query:
        :param filter:
        :param examples:
        :return: str レスポンスに含まれるquery_id
        """
        try:
            res = config.watson_discovery.add_training_data(config.environment_id, config.collection_id,
                                                            natural_language_query=query,
                                                            filter=filter, examples=examples)
            result = res.get_result()
            self.logger.debug(result)
            return result["query_id"]
        except ApiException as e:
            self.logger.debug(e.message)
            # すでに登録済みのクエリであれば、そのクエリIDを取得して返却する
            if e.message.startswith("ALREADY_EXISTS"):
                res = config.watson_discovery.list_training_data(config.environment_id, config.collection_id)
                for res_query in res.get_result()["queries"]:
                    if query == res_query["natural_language_query"]:
                        return res_query["query_id"]
            self.logger.warning("Watson Discoveryで例外が発生しました")
            import traceback
            traceback.print_exc()
            return None

    def create_training_example(self, query_id, document_id, cross_reference, relevance):
        """
        Discoveryのcreate_training_exampleメソッドを実行する
        :param query_id:
        :param document_id:
        :param cross_reference:
        :param relevance:
        :return: bool 処理成功すればTrue、失敗ならFalse
        """
        try:
            res = config.watson_discovery.create_training_example(config.environment_id, config.collection_id, query_id,
                                                                  document_id=document_id,
                                                                  cross_reference=cross_reference,
                                                                  relevance=relevance)
            self.logger.debug(res.get_status_code())
            self.logger.debug(res.get_result())
            if 200 <= res.get_status_code() <= 299:
                return True
            else:
                self.logger.warning(f"create_training_exampleでエラー応答がありました。{res.get_result()}")
                return False
        except ApiException as e:
            self.logger.debug(e.message)
            # すでに登録済みであればTrueを返す
            # TODO: すでに登録済みの場合、関連度を変更できたほうがいい
            if e.message.startswith("ALREADY_EXISTS"):
                return True
            self.logger.warning("Watson Discoveryで例外が発生しました")
            import traceback
            traceback.print_exc()
            return False
