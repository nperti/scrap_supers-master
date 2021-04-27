# -*- coding: utf-8 -*-

import datetime
import json
import os

import re

import scrapy
from bs4 import BeautifulSoup

from supers.items import PrecioItem
from supers.spiders.disco import HEADERS


this_path = os.path.realpath(__file__)

def get_categories():
    jumbo_file =  os.path.join(os.path.dirname(this_path), 'jumbo_cat.html')
    b = BeautifulSoup(open(jumbo_file).read())
    categories = sorted([i['href'] for i in b.find_all('a', {'class': 'item-link'})])
    leafs_categories = []
    for i in range(len(categories)-1):
        if not categories[i+1].startswith(categories[i]):
            leafs_categories.append(categories[i])
    leafs_categories.append(categories[-1])
    if '#' in leafs_categories:
        leafs_categories.remove('#')
    return leafs_categories


def has_layout(tag):
    return tag.has_attr('layout')

BUSCA_FMT = '/buscapagina?sl={layout}&PS=64&PageNumber=58&cc=18&sm=1&fq=C%3a%2f4%2f55%2f'
API_FMT = '/api/catalog_system/pub/products/search/?&fq={fq}&_from={start}&_to={end}'


class JumboSpider(scrapy.Spider):
    name = "jumbo"
    allowed_domains = ["jumbo.com.ar"]
    base_url = 'https://www.jumbo.com.ar'

    def get_url(self, path):
        return '{}/{}'.format(self.base_url, path)

    def start_requests(self):
        # needed to set some cookies from the server into our session
        yield scrapy.Request(url=self.base_url,
                             callback=self.parse_base)

    def parse_base(self, response):
        for category in get_categories():
            req = scrapy.Request(url=self.get_url(category), headers=HEADERS,
                                 callback=self.parse_category)
            yield req

    def parse_category(self, response):
        try:
            fq = re.findall("/buscapagina\?fq=([^&]+)", response.body)[0]
        except:
            fq = re.findall("/busca\?fq=([^&]+)", response.body)[0]
        req = scrapy.Request(url=self.get_url(API_FMT.format(fq=fq,start=0,end=49)))
        req.meta['pag'] = 1
        req.meta['fq'] = fq
        yield req

    def parse(self, response):
        items = json.loads(response.body)
        for p in items:
            description = p[u'productName']
            price = p["items"][0][u'sellers'][0][u'commertialOffer'][u"Price"]
            ean = p["items"][0]["ean"]
            _id = p[u'productReference']
            category = p.get('categories', [None])[0]
            brand = p.get('brand')
            date = datetime.date.today().isoformat()
            item = PrecioItem(price=price, description=description, _id=_id, date=date, category=category, brand=brand, ean=ean)
            yield item
        if len(items) == 50:
            i = response.meta['pag']
            fq = response.meta['fq']
            start = i * 50
            end = (i+1) * 50 - 1
            req = scrapy.Request(url=self.get_url(API_FMT.format(fq=fq, start=start, end=end)))
            req.meta['fq'] = fq
            req.meta['pag'] = i + 1
            yield req






