# -*- coding: utf-8 -*-
import datetime
import re

from bs4 import BeautifulSoup
import scrapy

from supers.items import PrecioItem


class CotodigitalSpider(scrapy.Spider):
    name = "cotodigital"
    allowed_domains = ["cotodigital3.com.ar"]

    def start_requests(self):
        # needed to set some cookies from the server into our session
        yield scrapy.Request(url='https://www.cotodigital3.com.ar/',
                             callback=self.parse_home)

    def parse_home(self, response):
        yield scrapy.Request(url='https://www.cotodigital3.com.ar/sitios/cdigi',
                             callback=self.parse_menus)

    def parse_menus(self, response):
        bs = BeautifulSoup(response.body)
        for menu in [cat.a['href'] for cat in bs.findAll('ul', {'class': 'sub_category'})]:
            req = scrapy.Request(url=response.urljoin(menu))
            req.meta['category'] = self._get_category(menu)
            req.meta['pag'] = 1
            yield req

    def _get_category(self, url):
        c = re.findall('catalogo-([^/]+)/', url)[0]
        # if not isinstance(url, unicode):
        #     t = urllib.unquote_plus(c)
        #     category = t.decode('utf8')
        # else:
        #     category = c
        return c

    def parse(self, response):
        bs = BeautifulSoup(response.body)
        prods = bs.find('ul', id='products')
        if prods is None:
            self.logger.info("Not products found in %s", response.url)
            return

        lis = prods.find_all('li')

        for prod in [l for l in lis if l.find('div')]:
            try:
                price = prod.find('span', {'class': 'atg_store_newPrice'}).text.replace('PRECIO CONTADO', '').strip().replace('$','')
            except:
                self.logger.info("Price not found at page, %s", response.url)
                continue
            price = price
            description = prod.find('div', 'descrip_full').text
            _id = prod.find('span', {'class': 'span_productName'}).div['id'].replace('descrip_container_sku','')
            date = datetime.date.today().isoformat()
            category = response.meta['category']
            yield PrecioItem(price=price, description=description, _id=_id, date=date, category=category)

        pag = response.meta['pag'] + 1
        a = bs.find('a', text=str(pag))
        if a is not None:
            req = scrapy.Request(url=response.urljoin(a['href']))
            req.meta['category'] = response.meta['category']
            req.meta['pag'] = pag
            yield req

