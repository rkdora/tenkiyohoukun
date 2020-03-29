import requests as rq
import json

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
