import json

import datetime
import logging

import scrapy
import time

from tutorial.items import JawboneItem

HEADERS = {
    "Authorization": "Bearer DudD7GQwFnfvLQR_tXA3zjp5WcekhpXi4gns0NkUyEaY2cnJQnJfspFdBeLmes3FnHGv14YiRz_SZK_iqV7QIVECdgRlo_GULMgGZS0EumxrKbZFiOmnmAPChBPDZ5JP"
}

SECONDS_IN_DAY = 86400
FIVE_MINUTES = 1.0 * 5.0 * 60.0 / SECONDS_IN_DAY


class JawboneSpider(scrapy.Spider):
    name = "jawbone"
    start_urls = [
        "http://google.com/"
    ]

    def parse(self, response):
        dates = get_dates()

        for date in dates:
            yield scrapy.Request("https://jawbone.com/nudge/api/v.1.1/users/@me/sleeps?date={date}".format(date=date),
                                 headers=HEADERS,
                                 callback=self.parse_sleep)

        for date in dates:
            yield scrapy.Request("https://jawbone.com/nudge/api/v.1.1/users/@me/meals?date={date}&limit=100".format(date=date),
                                 headers=HEADERS,
                                 callback=self.parse_meals)

        for date in dates:
            yield scrapy.Request("https://jawbone.com/nudge/api/v.1.1/users/@me/workouts?date={date}&limit=100".format(date=date),
                                 headers=HEADERS,
                                 callback=self.parse_workouts)

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

        for prev_item,sleep_tick_item,next_item in neighborhood(jsonresponse['data']['items']):
            item = JawboneItem()

            item.update(sleep_item)
            item['type'] = 'tick'
            item['depth'] = sleep_tick_item['depth']
            item['type_with_subtype'] = item['type'] + '_' + str(item['depth'])
            item['date'] = time.strftime('%Y-%m-%d', time.localtime(sleep_tick_item['time']))
            item['time'] = time.strftime('%H:%M:%S', time.localtime(sleep_tick_item['time']))

            if not next_item is None:
                item['duration'] = float(next_item['time'] - sleep_tick_item['time']) / SECONDS_IN_DAY
            else:
                item['duration'] = FIVE_MINUTES
            yield item

    def parse_meals(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for prev_item,meal_item,next_item in neighborhood(jsonresponse['data']['items']):
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

    def parse_workouts(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for prev_item,workout_item,next_item in neighborhood(jsonresponse['data']['items']):
            item = JawboneItem()

            item['type'] = 'workout'
            item['type_with_subtype'] = 'workout'
            if workout_item['sub_type'] == 3:
                item['type_with_subtype'] = 'workout_weights'
            item['title'] = workout_item['title']
            item['xid'] = workout_item['xid']
            workout_started = workout_item['time_created']
            item['date'] = time.strftime('%Y-%m-%d', time.localtime(workout_started))
            item['time'] = time.strftime('%H:%M:%S', time.localtime(workout_started))
            item['duration'] = float(workout_item['time_completed'] - workout_item['time_created']) / SECONDS_IN_DAY
            yield item


class JawboneSummarySpider(scrapy.Spider):
    name = "jawbone_summary"
    start_urls = [
        "http://google.com/"
    ]

    def parse(self, response):
        dates = get_dates()

        for date in dates:
            yield scrapy.Request("https://jawbone.com/nudge/api/v.1.1/users/@me/trends?end_date={date}&num_buckets=1".format(date=date),
                                 headers=HEADERS,
                                 callback=self.parse_trends)

    def parse_trends(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for trend_item in jsonresponse['data']['data']:
            trend_item_date = trend_item[0]
            trend_item_data = trend_item[1]
            item = JawboneItem()
            item['type'] = 'distance'
            item['date'] = trend_item_date
            item['distance'] = trend_item_data['m_distance']
            item['sleep_duration'] = seconds_to_hours(trend_item_data['s_duration'])
            item['sleep_bedtime'] = seconds_to_hours(trend_item_data['s_bedtime'])
            item['sleep_quality'] = trend_item_data['s_quality']

            yield item


def get_dates():
    start_date = datetime.datetime.strptime('20160413', "%Y%m%d").date()
    end_date = datetime.date.today()
    running_date = start_date
    dates = [running_date.strftime('%Y%m%d')]
    while running_date < end_date:
        running_date = running_date + datetime.timedelta(days=1)
        dates.append(running_date.strftime('%Y%m%d'))
    return dates


def neighborhood(iterable):
    iterator = iter(iterable)
    prev = None
    item = iterator.next()  # throws StopIteration if empty.
    for next in iterator:
        yield (prev,item,next)
        prev = item
        item = next
    yield (prev,item,None)


def seconds_to_hours(val):
    if (val is None):
        return None
    return float(val) / 60 / 60

