import urllib
import urllib2
import logging
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import json


CENTER_WEEKLY_URL = "http://www.center-gasztro.com/etlap.php?id=1"
CENTER_ENCODING = "windows-1250"
SLACK_VALIDATION_TOKEN = u"Ci4ASmor4GlgetBaR8F6MSl1"


def get_centerfood_data():

  user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
  values = {'name': 'Starschema Slack',
           'language': 'Python'}
  headers = {'User-Agent': user_agent}
  data = urllib.urlencode(values)
  request = urllib2.Request(CENTER_WEEKLY_URL, data, headers)
  response = urllib2.urlopen(request)

  return response.read().decode(CENTER_ENCODING)


def strip_line(line):

  return line.replace('\\n', '')\
      .replace('\t', ' ')\
      .replace('\\r', ' ')\
      .replace('\\r\\n', ' ')\
      .strip()


def get_foods(soup):

  ret_json_formatted = dict()
  ret_json_formatted["attachments"] = list()
  food_type_colors = ["#116747", "#7c8a0f", "#253935", "#116747", "#DDD600", "#018086",\
                      "#FFDEA8", "#116747", "#7c8a0f", "#3f1767", "#116747", "#DDD600",\
                      "#018086", "#FFDEA8"]

  for outer_tr_id, outer_tr in enumerate(soup.find_all('tr')):
    for outer_td_id, outer_td in enumerate(outer_tr.find_all('td')):
      if outer_tr_id == 4 and outer_td_id == 0:

      # real table starts here
        for t in outer_td.find_all('table'):
          for tr_id, tr in enumerate(t.find_all('tr')):
            food_type = None
            food_type_formatted = dict()
            foods = list()
            for td_id, td in enumerate(tr.find_all('td')):
              for f in td.find_all('font'):
                if td_id == 0 and len(f.text) > 1:
                  food_type = f.text
                  food_type_formatted["title"] = f.text
                  food_type_formatted["color"] = food_type_colors.pop()

                if td_id == datetime.today().weekday() + 1 and tr_id != 0:
                  map(lambda line: foods.append({ "value": strip_line(line) }), f.text.split('\r\n'))

                food_type_formatted["fields"] = foods
            if food_type is not None:
              ret_json_formatted["attachments"].append(food_type_formatted)

  return ret_json_formatted

def lambda_handler(event, context):
  logging.basicConfig(format='[%(levelname)s] %(asctime)s %(name)s %(filename)s:%(lineno)s - %(message)s',
      level=logging.DEBUG)

  try:

    if event is None:
      raise Exception("Failed to find event data, am I running in AWS?")

    if u'token' not in event:
      raise Exception("Failed to find authentication token, exit!")

    if event[u'token'] != SLACK_VALIDATION_TOKEN:
      raise Exception("Bad authentication token (%s), exit!" % event[u'token'])

    # return "So many sorriez, there is no Centerfood between 2017.06.15 and 2017.09.15 ;("

    content = get_centerfood_data()
    logging.debug("Parsing HTML content..")
    soup = BeautifulSoup(content, 'html.parser')

    return get_foods(soup)

  except urllib2.HTTPError as exc:
    logging.error("Error: %s %s" % (exc.code, exc.reason))
    sys.exit(1)
  except Exception as exc:
    logging.error("Error: %s" % str(exc))
    sys.exit(1)
  else:
    sys.exit(0)

if __name__ == '__main__':
  print json.dumps(lambda_handler({"token": SLACK_VALIDATION_TOKEN}, None), indent=4, ensure_ascii=False).encode('utf-8')


