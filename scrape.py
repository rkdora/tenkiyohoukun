import requests as rq
from bs4 import BeautifulSoup as bs4

url = 'http://weather.livedoor.com/forecast/rss/primary_area.xml'

path_w = 'city_list.txt'

res = rq.get(url)
soup = bs4(res.content, 'xml')

city_tags = soup.find_all('city')

city_list = []

for city in city_tags:
    city_list.append(city['title'] + ':' + city['id'])

with open(path_w, mode='w') as f:
    f.write('\n'.join(city_list))
    f.write('\n')
