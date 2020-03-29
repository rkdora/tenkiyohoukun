from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)
import os

import requests as rq
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def get_weather_info(city_num):
    url = 'http://weather.livedoor.com/forecast/webservice/json/v1?'
    city_params = {'city': city_num}
    data = rq.get(url, params=city_params)
    content = json.loads(data.text)

    content_title = format(content['title'])
    content_text = format(content['description']['text'])
    content_time = format(content['description']['publicTime'])\
                    .replace('T', ' ').replace('-', '/')[:-5]

    return content_title + '\n\n' + content_text + '\n\n最終更新日時：' + content_time


# モデル作成
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    num = db.Column(db.String(80))

    def __init__(self, name, num):
        self.name = name
        self.num = num


def register_city(city_name, city_num):
    all_city = db.session.query(City).filter(City.name==city_name).all()
    print(all_city)
    print(len(all_city))

    # reg = City(city_name, city_num)
    # db.session.add(reg)
    # db.session.commit()



@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    if text in '一覧':
        register_city('久留米', '400040')
        message = '一覧'
    else:
        city_num = '400040'
        message = wt.get_weather_info(city_num)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
