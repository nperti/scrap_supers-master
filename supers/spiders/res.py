# -*- coding: utf-8 -*-
import datetime
import re
import urlparse

from bs4 import BeautifulSoup
import scrapy

from supers.items import PrecioItem


class ResSpider(scrapy.Spider):
    name = "res"
    allowed_domains = ["res.com.ar"]

    start_urls = ['https://tienda.res.com.ar/carnes-vacunas.html?product_list_limit=all',
                  'https://tienda.res.com.ar/aves.html?product_list_limit=all',
                  'https://tienda.res.com.ar/cerdo.html?product_list_limit=all',
                  'https://tienda.res.com.ar/preparados.html?product_list_limit=all',
                  'https://tienda.res.com.ar/embutidos-y-achuras.html?product_list_limit=all',
                  'https://tienda.res.com.ar/quesos-y-fiambres.html?product_list_limit=all',
                  ]

    def parse(self, response):
        bs = BeautifulSoup(response.body)

        category = urlparse.urlparse(response.url).path[1:-5]
        for info in bs.findAll('div', {'class': 'product-item-info'}):
            _id = info.find('a')['href'].split('/')[-1].replace('.html', '')
            description = info.find('strong').text.strip().split('\n')[0].strip()
            price = info.find('span', {'data-price-type': 'finalPrice'}).text.replace('$','').strip()
            if info.find('script'):
                c = info.find('script').contents[0]
                a, b = re.search('"priceByWeight":\{"amount":([^,]+), "weight": ([^}]+)', c).groups()
                p, w = float(a), float(b)
                price = p / w
            date = datetime.date.today().isoformat()
            sale = len(info.find('div', {'class': 'product-grid-flags'}).find_all()) == 1
            # unidad = info.find('span', {'class': 'price-by'}).text.replace('$','').strip()
            yield PrecioItem(price=price, description=description, _id=_id, date=date, sale_type=sale, category=category)

