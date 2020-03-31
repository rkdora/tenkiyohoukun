from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ConfirmTemplate, PostbackAction,
    PostbackEvent
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

    if my_city:
        old_my_city_id = my_city.city_id
        my_city.city_id = city_id
        db.session.commit()
        message = '【旧】' + city_dict[old_my_city_id] + '\n【新】' + city_dict[city_id] +'\n更新しました'
    else:
        reg = MyCity(user_id, city_id)
        db.session.add(reg)
        db.session.commit()
        message = city_dict[city_id] + 'を登録しました'

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


@handler.add(PostbackEvent)
def handle_postback(event):
    postback_data = event.postback.data
    if postback_data == 'no':
        text_message = 'かしこまりました'
    else:
        user_id = event.source.user_id
        text_message = register_mycity(user_id, postback_data)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text_message))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    if user_message in city_dict:
        city_id = city_dict[user_message]
        text_message = get_weather_info(city_id)

        my_city = db.session.query(MyCity).filter(MyCity.user_id==event.source.user_id).first()
        if my_city:
            text_message = '現在、' + city_dict[mycity.city_id] +'が登録されています。\n' + user_message + 'に更新しますか？'
        else:
            text_message = user_message + 'を登録しますか？'

        confirm_template_message = TemplateSendMessage(
            alt_text='Confirm template',
            template=ConfirmTemplate(
                text=text_message,
                actions=[
                    PostbackAction(
                        label='はい',
                        display_text='はい',
                        data=city_id
                    ),
                    PostbackAction(
                        label='いいえ',
                        display_text='いいえ',
                        data='no'
                    )
                ]
            )
        )
        messages = [TextSendMessage(text=text_message), confirm_template_message]
    else:
        text_message = '対応していません。'
        messages = [TextSendMessage(text=text_message)]

    line_bot_api.reply_message(
        event.reply_token,
        messages)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
