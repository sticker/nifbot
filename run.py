import os
import logging
import json
from flask import Flask, request
from slackeventsapi import SlackEventAdapter
from lib.slack.slack import Slack
from lib.nifbot.mention_handler import MentionHandler


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
    logging.debug(request.form["payload"])
    form_json = json.loads(request.form["payload"])

    channel = form_json["channel"]["id"]
    page_url = form_json["actions"][0]["value"]
    text = f"{page_url} がクリックされました！"
    # slack_client.chat_postMessage(channel=channel, text=text)
    logging.debug(text)
    return "ok"


slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)


@slack_events_adapter.on("message")
def handle_message(event_data):
    event = event_data["event"]
    if "im" == event.get("channel_type"):
        mention_process(event_data)
    return "ok"


@slack_events_adapter.on("app_mention")
def handle_app_mention(event_data):
    mention_process(event_data)
    return "ok"


# Create an event listener for "reaction_added" events and print the emoji name
@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    logging.debug(event_data)
    event = event_data["event"]

    if event["user"] == "U01901QJX47":
        logging.debug("botのメッセージのため無視")
        return "ok"

    channel = event["item"]["channel"]
    emoji = event_data["event"]["reaction"]
    logging.debug(emoji)
    # text = f":{emoji}: リアクションありがとう！"
    # slack_client.chat_postMessage(channel=channel, text=text)
    # ts = message["item"]["ts"]
    # slack_client.reactions_add(name="robot_face", channel=channel, timestamp=ts)
    return "ok"


# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    logging.error("ERROR: " + str(err))


def mention_process(event_data):
    logging.debug(event_data)
    event = event_data["event"]

    if event.get("bot_profile") is not None:
        logging.debug("botのメッセージのため無視")
        return

    event_type = event.get("type")
    event_user = event.get("user")
    event_text = event.get("text")
    event_ts = event.get("ts")
    event_channel = event.get("channel")
    event_event_ts = event.get("event_ts")

    slack = Slack(event_type, event_user, event_text, event_ts, event_channel, event_event_ts)

    MentionHandler().mention_handler(slack)
    return


def main():
    # flask app起動
    app.run(port=8000)


if __name__ == "__main__":
    main()

