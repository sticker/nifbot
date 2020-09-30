import os
import logging
import json
from flask import Flask, request, make_response
from slackeventsapi import SlackEventAdapter
from lib.slack.slack import Slack
from lib.nifbot.mention_handler import MentionHandler
from lib.nifbot.reaction_handler import ReactionHandler
from lib.nifbot.interactive_handler import InteractiveHandler


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - [%(levelname)s] (%(threadName)-10s) {%(filename)s:%(lineno)d} %(message)s',
                    )

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
app = Flask(__name__)


# Health check
@app.route('/', methods=['GET', 'POST'])
def hello():
    return "ok"


# interactive message
@app.route('/slack/interactive', methods=['GET', 'POST'])
def interactive_handler():
    payload = json.loads(request.form["payload"])
    logging.debug(payload)
    type = payload["type"]

    if type != "interactive_message":
        return make_response("", 200)

    handler = InteractiveHandler()
    callback_id = payload["callback_id"]

    # callback_idごとに処理を分岐し、インタラクティブハンドラに委譲する
    if callback_id == "nifbot_knowledge_like":
        user = payload["user"]["id"]
        channel = payload["channel"]["id"]
        action_ts = payload["action_ts"]
        message_ts = payload["message_ts"]
        action = payload["actions"][0]

        slack = Slack(type, user, None, action_ts, channel, message_ts)
        handler.nifbot_knowledge_like(slack, action)

    return make_response("", 200)


# event
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)


@slack_events_adapter.on("message")
def handle_message(event_data, request):
    event = event_data["event"]
    if "im" == event.get("channel_type"):
        mention_process(event_data, request)
    return make_response("", 200)


@slack_events_adapter.on("app_mention")
def handle_app_mention(event_data, request):
    mention_process(event_data, request)
    return make_response("", 200)


# Create an event listener for "reaction_added" events and print the emoji name
@slack_events_adapter.on("reaction_added")
def reaction_added(event_data, request):
    reaction_process(event_data, request)
    return make_response("", 200)


# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    logging.error("ERROR: " + str(err))


# mention
def mention_process(event_data, request):
    """
    botへのメンション（IM含む）に対する処理
    イベントデータを元にSlackインスタンスを作成し、メンションハンドラに処理を委譲する
    :param event_data: イベントデータ
    :param request: リクエスト
    :return: 処理しない場合はFalse
    """
    if request.headers.get('X-Slack-Retry-Num') is not None:
        logging.debug(f"リトライのリクエストのため無視します X-Slack-Retry-Num={request.headers.get('X-Slack-Retry-Num')}")
        return False

    logging.debug(event_data)
    event = event_data["event"]

    if event.get("bot_profile") is not None:
        logging.debug("botのメッセージのため無視")
        return False

    event_type = event.get("type")
    event_user = event.get("user")
    event_text = event.get("text")
    event_ts = event.get("ts")
    event_channel = event.get("channel")
    event_event_ts = event.get("event_ts")

    slack = Slack(event_type, event_user, event_text, event_ts, event_channel, event_event_ts)

    MentionHandler().mention_handler(slack)
    return True


# reaction
def reaction_process(event_data, request):
    """
    リアクション絵文字に対する処理
    イベントデータを元にSlackインスタンスを作成し、リアクションハンドラに処理を委譲する
    :param event_data: イベントデータ
    :param request: リクエスト
    :return: 処理しない場合はFalse
    """
    if request.headers.get('X-Slack-Retry-Num') is not None:
        logging.debug(f"リトライのリクエストのため無視します X-Slack-Retry-Num={request.headers.get('X-Slack-Retry-Num')}")
        return False

    logging.debug(event_data)
    event = event_data["event"]

    # if event["user"] == "U01901QJX47":
    #     logging.debug("botのメッセージのため無視")
    #     return make_response("", 200)

    event_type = event.get("type")
    event_user = event.get("user")
    event_text = event.get("text")
    event_ts = event.get("ts")
    event_event_ts = event.get("event_ts")
    event_reaction = event.get("reaction")
    event_channel = event["item"].get("channel")
    event_item_ts = event["item"].get("ts")

    slack = Slack(event_type, event_user, event_text, event_ts, event_channel, event_event_ts, event_reaction)

    ReactionHandler().reaction_handler(slack)
    return True


def main():
    # flask app起動
    app.run(host='0.0.0.0', port=8000)


if __name__ == "__main__":
    main()

