import json
import config
from lib import get_logger


class WatsonAssistant:
    def __init__(self):
        self.logger = get_logger(__name__)

    def message_stateless(self, text):
        response = config.watson_assistant.message_stateless(
            assistant_id=f'{config.assistant_id}',
            input={
                'message_type': 'text',
                'text': text
            }).get_result()

        self.logger.debug(json.dumps(response, indent=2))
        return response['output']['generic'][0]['text']
