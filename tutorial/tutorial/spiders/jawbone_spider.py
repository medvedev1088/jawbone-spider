import json

import scrapy
import time

from tutorial.items import DmozItem
from tutorial.items import JawboneSleepItem
from tutorial.items import JawboneSleepTickItem

HEADERS = {
    "Authorization": "Bearer DudD7GQwFnfvLQR_tXA3zjp5WcekhpXi4gns0NkUyEaY2cnJQnJfspFdBeLmes3FnHGv14YiRz_SZK_iqV7QIVECdgRlo_GULMgGZS0EumxrKbZFiOmnmAPChBPDZ5JP"
}

class JawboneSpider(scrapy.Spider):
    name = "jawbone"
    start_urls = [
        "https://google.com/"
    ]

    def parse(self, response):
        for date in ["20160413", "20160414", "20160415", "20160416", "20160417", "20160418"]:
            yield scrapy.Request("https://jawbone.com/nudge/api/v.1.1/users/@me/sleeps?date={date}".format(date=date),
                                 headers=HEADERS,
                                 callback=self.parse_sleep)


    def parse_sleep(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for sleep_item in jsonresponse['data']['items']:
            xid = sleep_item['xid']
            item = JawboneSleepItem()
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
            item = JawboneSleepTickItem()

            item.update(sleep_item)
            item['depth'] = sleep_tick_item['depth']
            item['date'] = time.strftime('%Y-%m-%d', time.localtime(sleep_tick_item['time']))
            item['time'] = time.strftime('%H:%M:%S', time.localtime(sleep_tick_item['time']))

            if not next_item is None:
                item['duration'] = float(next_item['time'] - sleep_tick_item['time']) / 86400
            else:
                item['duration'] = 1.0 / 86400
            yield item

    def neighborhood(self, iterable):
        iterator = iter(iterable)
        prev = None
        item = iterator.next()  # throws StopIteration if empty.
        for next in iterator:
            yield (prev,item,next)
            prev = item
            item = next
        yield (prev,item,None)



