import json

import datetime
import logging

import scrapy
import time

from tutorial.items import DmozItem
from tutorial.items import JawboneItem

HEADERS = {
    "Authorization": "Bearer DudD7GQwFnfvLQR_tXA3zjp5WcekhpXi4gns0NkUyEaY2cnJQnJfspFdBeLmes3FnHGv14YiRz_SZK_iqV7QIVECdgRlo_GULMgGZS0EumxrKbZFiOmnmAPChBPDZ5JP"
}

FIVE_MINUTES = 1.0 * 5.0 * 60.0 / 86400

class JawboneSpider(scrapy.Spider):
    name = "jawbone"
    start_urls = [
        "https://google.com/"
    ]

    def parse(self, response):
        logging.info("This is a warning")
        start_date = datetime.datetime.strptime('20160413', "%d%m%Y").date()
        end_date = datetime.date.today()

        current_date = start_date
        dates = [time.strftime('%Y%m%d', time.localtime(current_date))]
        while current_date < end_date:
            current_date = current_date + datetime.timedelta(days=1)
            dates.append(time.strftime('%Y%m%d', time.localtime(current_date)))

        print "Crawling data for: " + str(dates)

        for date in dates:
            yield scrapy.Request("https://jawbone.com/nudge/api/v.1.1/users/@me/sleeps?date={date}".format(date=date),
                                 headers=HEADERS,
                                 callback=self.parse_sleep)

        for date in dates:
            yield scrapy.Request("https://jawbone.com/nudge/api/v.1.1/users/@me/meals?date={date}&limit=100".format(date=date),
                                 headers=HEADERS,
                                 callback=self.parse_meals)


    def parse_sleep(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for sleep_item in jsonresponse['data']['items']:
            xid = sleep_item['xid']
            item = JawboneItem()
            item['type'] = 'sleep'
            item['title'] = sleep_item['title']
            item['xid'] = xid

            request = scrapy.Request("https://jawbone.com/nudge/api/v.1.1/sleeps/{xid}/ticks".format(xid=xid),
                                 headers=HEADERS,
                                 callback=self.parse_sleep_tick)
            request.meta['sleep_item'] = item
            yield request

    def parse_sleep_tick(self, response):
        sleep_item = response.meta['sleep_item']

        jsonresponse = json.loads(response.body_as_unicode())

        for prev_item,sleep_tick_item,next_item in self.neighborhood(jsonresponse['data']['items']):
            item = JawboneItem()

            item.update(sleep_item)
            item['type'] = 'tick'
            item['depth'] = sleep_tick_item['depth']
            item['type_with_subtype'] = item['type'] + '_' + str(item['depth'])
            item['date'] = time.strftime('%Y-%m-%d', time.localtime(sleep_tick_item['time']))
            item['time'] = time.strftime('%H:%M:%S', time.localtime(sleep_tick_item['time']))

            if not next_item is None:
                item['duration'] = float(next_item['time'] - sleep_tick_item['time']) / 86400
            else:
                item['duration'] = FIVE_MINUTES
            yield item

    def parse_meals(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for prev_item,meal_item,next_item in self.neighborhood(jsonresponse['data']['items']):
            item = JawboneItem()

            item['type'] = 'meal'
            item['type_with_subtype'] = 'meal'
            if meal_item['title'] == 'Water':
                item['type_with_subtype'] = 'meal_water'
            item['title'] = meal_item['title']
            item['xid'] = meal_item['xid']
            item['date'] = time.strftime('%Y-%m-%d', time.localtime(meal_item['time_completed']))
            item['time'] = time.strftime('%H:%M:%S', time.localtime(meal_item['time_completed']))
            item['duration'] = FIVE_MINUTES
            yield item

        if not jsonresponse['links']['next'] is None:
            yield scrapy.Request(jsonresponse['links']['next'],
                                 headers=HEADERS,
                                 callback=self.parse_meals)

    def neighborhood(self, iterable):
        iterator = iter(iterable)
        prev = None
        item = iterator.next()  # throws StopIteration if empty.
        for next in iterator:
            yield (prev,item,next)
            prev = item
            item = next
        yield (prev,item,None)



