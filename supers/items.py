# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PrecioItem(scrapy.Item):
    description = scrapy.Field()
    price = scrapy.Field()
    _id = scrapy.Field()
    category = scrapy.Field()
    brand = scrapy.Field()
    date = scrapy.Field()
    sale_type = scrapy.Field()
    sale_value = scrapy.Field()
    ean = scrapy.Field()
