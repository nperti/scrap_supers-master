# -*- coding: utf-8 -*-

import datetime
import json
import re

from bs4 import BeautifulSoup
import scrapy

from supers.items import PrecioItem


HEADERS = {
    'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
    'Content-type': 'application/json; charset=UTF-8',
    'Accept': 'application/json, text/plain',
}


class DiscoSpider(scrapy.Spider):
    name = "disco"
    allowed_domains = ["disco.com.ar"]
    regex_menu = re.compile('.*Array\((?P<id>\d{1,5}),\'(?P<categoria>.*)\',null.*')
    base_url = 'https://www.disco.com.ar'

    def get_url(self, path):
        return '{}/{}'.format(self.base_url, path)

    def start_requests(self):
        # needed to set some cookies from the server into our session
        yield scrapy.Request(url=self.base_url,
                             callback=self.parse_base)

#     def parse_base(self, response):
#         yield scrapy.Request(url='https://www.jumbo.com.ar/Login/PreHome.aspx',
#                              callback=self.parse_prehome)
#
#     def parse_prehome(self, response):
    def parse_base(self, response):
        yield scrapy.Request(url=self.get_url('Login/Invitado.aspx'),
                             callback=self.parse_login)

    def parse_login(self, response):
        yield scrapy.Request(url=self.get_url('Comprar/Menu.aspx?SId=ie4i2u52024'),
                             callback=self.parse_menu)

    def parse_menu(self, response):
        menu = self.regex_menu.findall(response.body)

        for _id, _ in menu:
            data = {'IdMenu': _id,
                    'textoBusqueda': '', 'producto': '', 'marca': '', 'pager': '',
                    'precioDesde': '', 'precioHasta': '', 'ordenamiento': 0}
            req = scrapy.Request(url=self.get_url('Comprar/HomeService.aspx/ObtenerArticulosPorDescripcionMarcaFamiliaLevex'),
                                 method='POST', body=json.dumps(data),
                                 headers=HEADERS)
            yield req

    def parse(self, response):
        r = json.loads(json.loads(response.body)['d'])
        items = r['ResultadosBusquedaLevex']

        for p in items:
            description = p['DescripcionArticulo']
            price = p['Precio']
            _id = p['IdArticulo']
            category = p['Grupo_Tipo']
            brand = p['Grupo_Marca']
            date = datetime.date.today().isoformat()
            item = PrecioItem(price=price, description=description, _id=_id, date=date, category=category, brand=brand)

            if p['Descuentos']:
                item['sale_type'] = p['Descuentos'][0]['Tipo']
                item['sale_value'] = p['Descuentos'][0]['Subtipo']

            yield item
