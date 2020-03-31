import requests as rq
from bs4 import BeautifulSoup as bs4
import pickle

url = 'http://weather.livedoor.com/forecast/rss/primary_area.xml'

path = 'city_dict.pickle'

res = rq.get(url)
soup = bs4(res.content, 'xml')

city_tags = soup.find_all('city')

city_dict = {}

for city in city_tags:
    city_dict[city['title']] = city['id']

print(city_dict)

with open(path, mode='wb') as f:
        pickle.dump(city_dict,f)
