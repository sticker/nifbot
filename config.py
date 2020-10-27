import os
import ibm_boto3
from ibm_botocore.client import Config
from ibm_watson import DiscoveryV1, AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


# for IBM Watson Assistant
watson_assistant_api_key = os.getenv('WATSON_ASSISTANT_API_KEY')
watson_assistant_api_version = os.getenv('WATSON_ASSISTANT_API_VERSION', '2019-04-30')
watson_assistant_service_url = os.getenv('WATSON_ASSISTANT_SERVICE_URL',
                                 'https://api.jp-tok.assistant.watson.cloud.ibm.com/instances/fcc084f6-7d87-4164-8cb5-5f1ee62a5aa4')
watson_assistant_authenticator = IAMAuthenticator(f'{watson_assistant_api_key}')
watson_assistant = AssistantV2(
    version=f'{watson_assistant_api_version}',
    authenticator=watson_assistant_authenticator
)
watson_assistant.set_service_url(f'{watson_assistant_service_url}')
assistant_id = '70ffd6a5-e13a-4753-afb8-df1ebdeabdae'  # nifbot

# for IBM Watson Discovery
watson_discovery_api_key = os.getenv('WATSON_DISCOVERY_API_KEY')
watson_discovery_version = os.getenv('WATSON_DISCOVERY_API_VERSION', '2019-04-30')
watson_discovery_service_url = os.getenv('WATSON_DISCOVERY_SERVICE_URL',
                                         'https://api.jp-tok.discovery.watson.cloud.ibm.com/instances/7d9df5db-5015-4ce0-b48d-22480586e18e')
watson_discovery_authenticator = IAMAuthenticator(f'{watson_discovery_api_key}')
watson_discovery = DiscoveryV1(
    version=f'{watson_discovery_version}',
    authenticator=watson_discovery_authenticator
)
watson_discovery.set_service_url(f'{watson_discovery_service_url}')
environment_id = os.getenv('WATSON_DISCOVERY_ENVIRONMENT_ID', 'cf8a6b24-49aa-4aa3-81cd-b44c1518d549')
collection_id = os.getenv('WATSON_DISCOVERY_COLLECTION_ID', 'c1e25d6d-c79e-4b47-9ab4-cf6dfcdcf8d3')
# discovery.queryでの検索結果件数
results_count = 3
# 返答としてpassageを採用するscoreのしきい値
passage_score_threshold = 20
passages_count = 1
passages_characters = 100

# for IBM Cloud Object Storage
# Constants for IBM COS values
COS_ENDPOINT = os.getenv('COS_ENDPOINT', "https://s3.jp-tok.cloud-object-storage.appdomain.cloud")
COS_API_KEY_ID = os.getenv('COS_API_KEY_ID', "pcd5Nt_kW09ilV61KaYTIoIxnKhmRtXwryeasOHkVauo")
COS_AUTH_ENDPOINT = os.getenv('COS_AUTH_ENDPOINT', "https://iam.cloud.ibm.com/identity/token")
COS_RESOURCE_CRN = os.getenv('COS_RESOURCE_CRN',
                             "crn:v1:bluemix:public:cloud-object-storage:global:a/941b962884254952b3d8dd7bcb34fcfe:dc3ed5ea-b874-4b47-a6e5-96e628b4fb78::")
# Create resource
cos = ibm_boto3.resource("s3",
                         ibm_api_key_id=COS_API_KEY_ID,
                         ibm_service_instance_id=COS_RESOURCE_CRN,
                         ibm_auth_endpoint=COS_AUTH_ENDPOINT,
                         config=Config(signature_version="oauth"),
                         endpoint_url=COS_ENDPOINT
                         )
