import scrapy

class DmozItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    desc = scrapy.Field()

class JawboneSleepItem(scrapy.Item):
    xid = scrapy.Field()
    title = scrapy.Field()

class JawboneSleepTickItem(JawboneSleepItem):
    depth = scrapy.Field()
    date = scrapy.Field()
    time = scrapy.Field()
    duration = scrapy.Field()