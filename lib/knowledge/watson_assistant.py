import json
import re
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from ibm_watson import DiscoveryV1, AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from lib import get_logger, app_home


class WatsonAssistant:
    def __init__(self):
        self.logger = get_logger(__name__)
        # for IBM Watson Assistant
        apikey = '-JodsJcPEAR2uHMVakxtw4XVqq8dNqScKBc1cUhFUAmo'
        version = '2019-04-30'
        url = 'https://api.au-syd.assistant.watson.cloud.ibm.com/instances/c00b23f8-a5b0-458b-a868-95d795c7f4b2'

        authenticator = IAMAuthenticator(f'{apikey}')
        self.assistant = AssistantV2(
            version=f'{version}',
            authenticator=authenticator
        )

        self.assistant.set_service_url(f'{url}')
        self.assistant_id = 'f5cb09d1-341e-4392-8bf9-92cef5249ebc'  # nifbot-test

    def message_stateless(self, text):
        response = self.assistant.message_stateless(
            assistant_id=f'{self.assistant_id}',
            input={
                'message_type': 'text',
                'text': text
            }).get_result()

        self.logger.debug(json.dumps(response, indent=2))
        return response['output']['generic'][0]['text']
