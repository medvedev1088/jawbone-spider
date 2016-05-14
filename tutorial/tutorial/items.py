import scrapy


class DmozItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    desc = scrapy.Field()


class JawboneItem(scrapy.Item):
    type = scrapy.Field()
    type_with_subtype = scrapy.Field()
    xid = scrapy.Field()
    date = scrapy.Field()
    time = scrapy.Field()
    duration = scrapy.Field()
    title = scrapy.Field()
    depth = scrapy.Field()
    distance = scrapy.Field()
    sleep_duration = scrapy.Field()
    sleep_bedtime = scrapy.Field()
    sleep_quality = scrapy.Field()



