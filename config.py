import os
import ibm_boto3
from ibm_botocore.client import Config
from ibm_watson import DiscoveryV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# for IBM Watson Discovery
apikey = os.getenv('WATSON_DISCOVERY_API_KEY', 'zfLyg6DnAvMy7oDGMzOMj1LlJf9tDpo1SWwbb0inLYUE')
version = os.getenv('WATSON_DISCOVERY_API_VERSION', '2019-04-30')
url = os.getenv('WATSON_DISCOVERY_SERVICE_URL',
                'https://api.jp-tok.discovery.watson.cloud.ibm.com/instances/cba9436a-8e1c-412e-a2c1-36eaaedcbb87')
authenticator = IAMAuthenticator(f'{apikey}')
watson_discovery = DiscoveryV1(
    version=f'{version}',
    authenticator=authenticator
)
watson_discovery.set_service_url(f'{url}')
environment_id = os.getenv('WATSON_DISCOVERY_ENVIRONMENT_ID', '6155a670-d884-43aa-afd7-4d7c5880e3d1')
collection_id = os.getenv('WATSON_DISCOVERY_COLLECTION_ID', 'd68786dd-10e7-4bf0-86fe-b840b434bd2c')
# discovery.queryでの検索結果件数
results_count = 5
# 返答としてpassageを採用するscoreのしきい値
passage_score_threshold = 20
passages_count = 1
passages_characters = 100


# for IBM Cloud Object Storage
# Constants for IBM COS values
COS_ENDPOINT = os.getenv('COS_ENDPOINT', "https://s3.jp-tok.cloud-object-storage.appdomain.cloud")
COS_API_KEY_ID = os.getenv('COS_API_KEY_ID', "lrbBmMu1tBkWoxqt3ZvxrGmkRQMgaKa5eZp5LYyjVaoS")
COS_AUTH_ENDPOINT = os.getenv('COS_AUTH_ENDPOINT', "https://iam.cloud.ibm.com/identity/token")
COS_RESOURCE_CRN = os.getenv('COS_RESOURCE_CRN',
                             "crn:v1:bluemix:public:cloud-object-storage:global:a/1dc861249cb942efabf32f603d9b7671:c1a38fe9-ff82-487e-b4f5-05caeec8338a::")
# Create resource
cos = ibm_boto3.resource("s3",
                         ibm_api_key_id=COS_API_KEY_ID,
                         ibm_service_instance_id=COS_RESOURCE_CRN,
                         ibm_auth_endpoint=COS_AUTH_ENDPOINT,
                         config=Config(signature_version="oauth"),
                         endpoint_url=COS_ENDPOINT
                         )
