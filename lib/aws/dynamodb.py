from lib import get_logger
from logging import DEBUG, INFO, WARNING
from boto3 import Session
from boto3.dynamodb.conditions import Key, Contains, Attr
from botocore.exceptions import ClientError
from time import sleep
import os


class Dynamodb(object):
    CAPACITY_EXCEPTIONS = (
        "ValidationException",
    )

    RETRY_EXCEPTIONS = ('ProvisionedThroughputExceededException',
                        'ThrottlingException')
    RETRY_COUNT = 10

    def __init__(self):
        self.logger = get_logger(__name__)
        region_name = os.getenv('AWS_REGION', 'ap-northeast-1')
        # 環境変数 AWS_REGION が設定されていない場合は処理しない
        if region_name != '':
            session = Session(region_name=region_name)
            self.resource = session.resource('dynamodb')

    def insert(self, target, item):
        table = self.resource.Table(target)
        self.request_within_capacity(table, "put_item(Item=self.emptystr_to_none(param))", item)

    def remove(self, target, key):
        table = self.resource.Table(target)
        table.delete_item(Key=key)

    def truncate(self, target):
        self.logger.log(INFO, "%s のレコードをすべて削除します" % target)
        table = self.resource.Table(target)
        # データ全件取得
        delete_items = []
        parameters = {}
        ExclusiveStartKey = None
        while True:
            if ExclusiveStartKey is None:
                response = self.request_within_capacity(table, "scan()")
            else:
                response = self.request_within_capacity(table, "scan(ExclusiveStartKey=param)", ExclusiveStartKey)

            delete_items.extend(response["Items"])

            if ("LastEvaluatedKey" in response) is True:
                ExclusiveStartKey = response["LastEvaluatedKey"]
            else:
                break

        # キー抽出
        key_names = [x["AttributeName"] for x in table.key_schema]
        delete_keys = [{k: v for k, v in x.items() if k in key_names} for x in delete_items]

        # データ削除
        # with table.batch_writer() as batch:
        #     for key in delete_keys:
        #         batch.delete_item(Key=key)
        for key in delete_keys:
            self.logger.log(DEBUG, '%s を削除します' % key)
            self.request_within_capacity(table, "delete_item(Key=param)", key)

        self.logger.log(INFO, "%s のレコードをすべて削除しました" % target)
        return 0

    def scan(self, target):
        table = self.resource.Table(target)
        convert_items = []
        ExclusiveStartKey = None
        while True:
            if ExclusiveStartKey is None:
                response = self.request_within_capacity(table, "scan()")
            else:
                response = self.request_within_capacity(table, "scan(ExclusiveStartKey=param)", ExclusiveStartKey)

            items = response["Items"]
            for item in items:
                convert_items.append(self.none_to_emptystr(item))
            if ("LastEvaluatedKey" in response) is True:
                ExclusiveStartKey = response["LastEvaluatedKey"]
            else:
                break

        return convert_items

    def scan_specified_attr_value(self, tablename, attr_name, attr_value):
        fe = Key(attr_name).eq(attr_value)
        method_str = f"scan(FilterExpression=param"
        return self.request(tablename, method_str, fe)

    def request(self, tablename, method_str, param):
        """
        PKey、SKeyを指定してDynamoDBからデータを取得する
        :param tablename:
        :param method_str:
        :param kce:
        :return:
        """
        table = self.resource.Table(tablename)

        convert_items = []
        ExclusiveStartKey = None
        while True:
            if ExclusiveStartKey is not None:
                method_str += f", ExclusiveStartKey={ExclusiveStartKey}"

            method_str += ')'
            response = self.request_within_capacity(table, method_str, param)

            items = response["Items"]
            for item in items:
                convert_items.append(self.none_to_emptystr(item))
            if ("LastEvaluatedKey" in response) is True:
                ExclusiveStartKey = response["LastEvaluatedKey"]
            else:
                break

        return convert_items

    def query_specified_key_value(self, tablename, key, value, sortkey=None, sortvalue=None, indexname=None, scan_index_forward=True):
        kce = Key(key).eq(value)
        if sortkey and sortvalue:
            kce = kce & Key(sortkey).eq(sortvalue)

        indexname_param = ""
        if indexname is not None:
            indexname_param = f", IndexName='{indexname}'"

        method_str = f"query(KeyConditionExpression=param, ScanIndexForward={scan_index_forward}{indexname_param}"

        return self.request(tablename, method_str, kce)

    def emptystr_to_none(self, item):
        '''
        Boto3では空文字をDynamoDBに登録できないため、空文字をNoneに変換する
        see. https://qiita.com/t-fuku/items/0ad85c245f62883a4d11

        :param item:
        :return:
        '''
        for k, v in item.items():
            if isinstance(v, dict):
                self.emptystr_to_none(v)
            elif isinstance(v, list):
                for i in range(len(v)):
                    list_elem = v[i]

                    if isinstance(list_elem, str):
                        if list_elem == '':
                            v[i] = None
                    elif isinstance(list_elem, list) or isinstance(list_elem, dict):
                        self.emptystr_to_none(list_elem)
            elif isinstance(v, str):
                if v == '':
                    item[k] = None

        return item

    def none_to_emptystr(self, item):
        '''
        Boto3では空文字をDynamoDBに登録できないため、空文字をNoneに変換して登録している
        DynamoDBからデータを取得するときは、Noneを空文字に戻す
        see. https://qiita.com/t-fuku/items/0ad85c245f62883a4d11

        :param item:
        :return:
        '''
        for k, v in item.items():
            if isinstance(v, dict):
                self.none_to_emptystr(v)
            elif isinstance(v, list):
                for i in range(len(v)):
                    list_elem = v[i]

                    if list_elem is None:
                        v[i] = ''
                    elif isinstance(list_elem, list) or isinstance(list_elem, dict):
                        self.none_to_emptystr(list_elem)
            elif v is None:
                item[k] = ''

        return item

    def request_within_capacity(self, table, method_str, param=None):
        '''
        Tableオブジェクトのメソッド実行時にスループットキャパシティを超えたらリトライする
        スループットキャパシティが1000未満の場合は100ずつ増加させてリトライする
        スループットキャパシティが1000以上の場合はスリープしてリトライする
        :param table: Tableオブジェクト
        :param method_str: 実行したいメソッドの文字列（evalで実行される）
        :param param: method_str内で記述された "param" 部分に渡すオブジェクト
        :return: メソッド実行時のresponse
        '''
        retries = 0
        for i in range(self.RETRY_COUNT):
            try:
                response = eval("table.%s" % method_str)
                return response
            except ClientError as err:
                if err.response['Error']['Code'] not in self.RETRY_EXCEPTIONS:
                    raise
                else:
                    self.logger.log(INFO, 'DynamoDBのキャパシティを超えたためsleepしてリトライします retries=%d' % retries)
                    sleep(2 ** retries)
                    retries += 1

        return None

    def atomic_counter(self, table_name: str, prefix: str):
        """
        * アトミックカウンタ用テーブルをインクリメントして結果を返却する
        :param table_name:
        :param prefix:
        :param min_value:
        :param max_value:
        :return:
        """
        try:
            table = self.resource.Table(table_name)
            response = table.update_item(
                Key={
                    'prefix': prefix,
                },
                UpdateExpression="set atomic_counter = atomic_counter + :increase",
                ExpressionAttributeValues={
                    ':increase': int(1),
                },
                ReturnValues="UPDATED_NEW"
            )
            # インクリメント後のカウンター値を取得、取得できない場合は-1を返す
            atomic_counter = response.get('Attributes', {}).get('atomic_counter', -1)
            self.logger.debug(f"prefix={prefix}, atomic_counter={atomic_counter}")

            # カウンター値が取得できなければ例外処理へ
            if atomic_counter == -1:
                raise Exception("アトミックカウンタが取得できません。", f"prefix={prefix}", f"table_name={table_name}")

        except Exception as err:
            # その他エラー
            self.logger.error("{}".format(err))
            raise Exception("アトミックカウンタが取得できません。", f"prefix={prefix}", f"table_name={table_name}")

        return atomic_counter

    def update_by_key(self, tablename, key, value, update_key, update_value):
        table = self.resource.Table(tablename)
        try:
            method_str = f'update_item(\
                Key={{ \
                    "{key}": "{value}" \
                }},\
                UpdateExpression="set {update_key}=:update_value",\
                ExpressionAttributeValues=param,\
                ReturnValues="UPDATED_NEW"\
            )'

            param = dict()
            param[':update_value'] = update_value

            self.logger.debug(f"method_str={method_str}")
            response = self.request_within_capacity(table, method_str, param)
            return response
        except Exception as err:
            self.logger.error("{}".format(err))
            return None

    def save_akashi_token(self, tablename, slack_name, akashi_token, akashi_token_save_time):
        table = self.resource.Table(tablename)
        try:
            method_str = f'update_item(\
                            Key={{\
                                "slack_name": "{slack_name}"\
                            }},\
                            UpdateExpression="set akashi_token=:akashi_token, akashi_token_save_time=:akashi_token_save_time",\
                            ExpressionAttributeValues=param,\
                            ReturnValues="UPDATED_NEW"\
                        )'

            param = dict()
            param[':akashi_token'] = akashi_token
            param[':akashi_token_save_time'] = akashi_token_save_time\

            self.logger.debug(f"method_str={method_str}")
            response = self.request_within_capacity(table, method_str, param)
            return response
        except Exception as err:
            self.logger.error("{}".format(err))
            return None
