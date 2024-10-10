import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

client = WebClient(token="XXX")

# トークンが正しいか確認します
auth_test = client.auth_test()
bot_user_id = auth_test["user_id"]
print(f"App's bot user: {bot_user_id}")

try:
    filepath="./cat.jpg"
    response = client.files_upload_v2(channel_id='XXX', file=filepath, request_file_info=False)
    assert response["file"]  # the uploaded file
except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["ok"] is False
    assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
    print(f"Got an error: {e.response['error']}")
    print(f"{e}")

# import requests

# # ここでエラー（xxxx.comは仮）
# html = requests.get("https://www.google.co.jp/")

# print(html)

# import certifi
# print(certifi.where())