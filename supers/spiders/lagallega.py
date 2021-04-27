# -*- coding: utf-8 -*-
import datetime
import re
import urlparse
import urllib

from bs4 import BeautifulSoup
import scrapy
from scrapy.shell import inspect_response


from supers.items import PrecioItem


class LagallegaSpider(scrapy.Spider):
    name = "lagallega"
    allowed_domains = ["lagallega.com.ar"]
    base_url = 'http://www.lagallega.com.ar/'
    categorias = {}

    def start_requests(self):
        # needed to set some cookies from the server into our session
        yield scrapy.Request(url=self.base_url + 'index.asp',
                             callback=self.parse_index)

    def parse_index(self, response):
        yield scrapy.Request(url=self.base_url + 'Menu-1.asp',
                             callback=self.parse_menu)

    def parse_menu(self, response):
        bs = BeautifulSoup(response.body)
        for div in bs.find_all('div'):
            req = self.process_div(div)
            if req is not None:
                yield req

    def parse_productos(self, response):
        # inspect_response(response, self)
        bs = BeautifulSoup(response.body)
        category = response.request.meta['categoria']
        for div in bs.find_all('div', attrs={'class': 'InfoProd'}):

            if div.find('div', attrs={'class': 'OferProd'}):
                sale_type = 'Oferta'
                description = div.find('div', attrs={'class': 'desc'}).text.strip()
            else:
                sale_type = ''
                description = div.find('div', attrs={'class': 'InfoProdDet'}).text.strip()

            price = div.find('div', attrs={'class': 'precio'}).text.strip()[1:].replace(',', '.')
            date = datetime.date.today().isoformat()
            _id = div.find_all('div')[-1].get('id')[1:]
            item = PrecioItem(price=price, description=description, _id=_id, date=date,
                              category=category, sale_type=sale_type)
            yield item

        sig = bs.find('input', attrs={'value': 'Siguiente'})
        if sig is not None:
            onclick = sig.get('onclick')
            if onclick is not None:
                pre = len("FCargaP('#fArticulos','./")
                sig_link = onclick[pre:-3]
                req = scrapy.Request(url=self.base_url + sig_link,
                                      headers={'Referer': self.base_url + 'ccompra.asp'},
                                      callback=self.parse_productos)
                req.meta['categoria'] = category
                yield req

    def process_div(self, div):
        onclick = div.get('onclick')

        div2 = div.find('div')
        if div2 is not None and  div2.get('title') == 'Volver':
            return None

        if onclick is None:
            return None

        if onclick.startswith('Dispara('):
            cat = onclick[-5:-3]
            self.categorias[(cat, )] = div.text
            return scrapy.Request(url= self.base_url + 'Menu-2.asp?' +
                                       urllib.urlencode({'Niv1': cat}),
                                  headers={'Referer': self.base_url + 'ccompra.asp'},
                                  callback=self.parse_menu)

        if onclick.startswith('Dispara2('):
            n1, n2 = eval(onclick[8:-1])
            self.categorias[(n1, n2)] = div.text
            return scrapy.Request(url= self.base_url + 'Menu-3.asp?' +
                                       urllib.urlencode({'Niv1': n1, 'Niv2': n2}),
                                  headers={'Referer': self.base_url + 'ccompra.asp'},
                                  callback=self.parse_menu)

        if onclick.startswith('Dispara3('):
            n1, n2, n3 = eval(onclick[8:-1])
            self.categorias[(n1, n2, n3)] = div.text
            return scrapy.Request(url= self.base_url + 'Menu-4.asp?' +
                                       urllib.urlencode({'Niv1': n1, 'Niv2': n2, 'Niv3': n3}),
                                  headers={'Referer': self.base_url + 'ccompra.asp'},
                                  callback=self.parse_menu)

        if onclick.startswith("EnvioForm('Cat'"):
            n1, n2, n3, n4 = [eval(n) for n in onclick[:-1].split(',')[1:]]
            cat = tuple([n for n in [n1, n2, n3, n4] if n != '00'])
            self.categorias[cat] = div.text
            req = scrapy.Request(url=self.base_url + 'Productos.asp?' +
                                      urllib.urlencode({'N1': n1, 'N2': n2, 'N3': n3,
                                                        'N4': n4}),
                                  headers={'Referer': self.base_url + 'ccompra.asp'},
                                  callback=self.parse_productos)

            categorias = []
            for i in range(len(cat) - 1, -1, -1):
                if i == 0:
                    categorias.append(self.categorias[cat[0:]])
                else:
                    categorias.append(self.categorias[cat[0:-i]])

            req.meta['categoria'] = ' / '.join(categorias)
            return req