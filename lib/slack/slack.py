import os
from slack import WebClient


class Slack:
    def __init__(self, event_type, event_user, event_text, event_ts, event_channel, event_event_ts,
                 event_reaction=None):
        # Create a SlackClient for your bot to use for Web API requests
        slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
        self.client = WebClient(slack_bot_token)
        self.event_type = event_type
        self.event_user = event_user
        self.event_user_name = self.client.users_info(user=event_user).get("user").get("name")
        self.event_text = event_text
        self.event_ts = event_ts
        self.event_channel = event_channel
        self.event_event_ts = event_event_ts
        self.event_reaction = event_reaction

    def send(self, text, attachments=None, thread_ts=None):
        self.client.chat_postMessage(channel=self.event_channel, text=text, attachments=attachments, thread_ts=thread_ts)

    def reply(self, text, attachments=None, thread_ts=None):
        text = f'<@{self.event_user}> ' + text
        self.send(text, attachments=attachments, thread_ts=thread_ts)

    def reactions_add(self, name, channel, timestamp):
        self.client.reactions_add(name=name, channel=channel, timestamp=timestamp)
