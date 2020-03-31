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

import pickle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

city_path = 'city_dict.pickle'
with open(city_path, mode='rb') as f:
    city_dict = pickle.load(f)

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
class MyCity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80))
    city_id = db.Column(db.String(80))

    def __init__(self, user_id, city_id):
        self.user_id = user_id
        self.city_id = city_id


def register_mycity(user_id, city_id):
    my_city = db.session.query(MyCity).filter(MyCity.user_id==user_id).first()

    print('my_city', my_city)

    if my_city:
        reg = MyCity(user_id, city_id)
        db.session.add(reg)
        db.session.commit()
        message = '登録しました'
    else:
        my_city.city_id = city_id
        db.session.commit()
        message = '更新しました'

    return message

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
    user_message = event.message.text

    if user_message in '登録':
        user_id = event.source.user_id
        message = register_mycity(user_id, '400040')
    else:
        if user_message in city_dict:
            message = get_weather_info(city_dict[user_message])
        else:
            message = '対応していません。'

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
