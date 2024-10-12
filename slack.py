import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# https://tools.slack.dev/python-slack-sdk/web/

class SlackNotificator():
    def __init__(self):
        load_dotenv()
        self.SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
        self.SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')
        self.CLIENT = WebClient(token=self.SLACK_BOT_TOKEN)
        # https://api.slack.com/methods/auth.test
        self.AUTH_RESPONSE = self._test_authorize()  

    def _test_authorize(self):
        auth_test = self.CLIENT.auth_test()
        assert auth_test["ok"] is True

    def get_bot_user_id(self):
        return self.AUTH_RESPONSE["user_id"]
    
    def post_message(self, message: str):
        try:
            response = self.CLIENT.chat_postMessage(
                channel=self.SLACK_CHANNEL_ID,
                text=message
            )
            return response
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'

    def post_message_with_files(self, message: str, filepath: str):
        try:
            response = self.CLIENT.files_upload_v2(
                channel=self.SLACK_CHANNEL_ID,
                file=filepath,
                initial_comment=message,
            )
            return response
        except SlackApiError as e:
            assert e.response["error"]

if __name__ == "__main__": 
    notificator = SlackNotificator()
    message = "test message"
    filepath = "cat.jpg"
    notificator.post_message_with_files(message, filepath)