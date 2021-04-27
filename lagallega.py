
# -*- coding: utf-8 -*-
import logging
import requests
import json
import sys
import re

from bs4 import BeautifulSoup

from datetime import date
from utils import UnicodeCsvWriter

h1 = logging.StreamHandler(stream=sys.stdout)
h1.setLevel(logging.DEBUG)

logger = logging.getLogger('lagallega')
logger.addHandler(h1)
logger.setLevel(logging.DEBUG)

# all urls needed
URL = {
    'base': 'http://www.lagallega.com.ar',
    'prehome': '/login.asp',
    'login': '/CCompra.asp',
    'menu': '/CategLista.asp',
}


# utility to get the whole url
def url(name):
    return URL['base'] + URL[name]

# browser creation
browser = requests.Session()

# set a proper user agent
user_agent = {'User-agent': 'Mozilla/5.0'}
cookies = dict(cantP='40')

# needed to set some cookies from the server into our session
r = browser.get(URL['base'], headers=user_agent)
r = browser.get(url('prehome'), headers=user_agent)
r = browser.get(url('login'), headers=user_agent)
r = browser.get(url('menu'), headers=user_agent)

menu_bs = BeautifulSoup(r.content)


def has_class_n(tag):
    return 'N' == tag.get('class', ['-'])[0][0]


menu_divs = menu_bs.find_all(has_class_n)


fp = open('lagallega.csv', 'wb')
csvwriter = UnicodeCsvWriter(fp)
csvwriter.writerow(['desc', 'precio', 'plu', 'precio x unidad',
                    'link', 'imagen', 'rubro', 'fecha'])

menu = []
partial_name = []
for div in menu_divs:
    nivel = int(div.get('class')[0][1])
    partial_name = partial_name[:nivel-1]
    if div.get('onclick').startswith('parent.'):
        menu.append((' - '.join(partial_name + [div.text]),
                     div.get('onclick').split('=', 1)[1][1:-1]))
    else:
        partial_name.append(div.text)


def scrap_page(category, link):
    r = browser.get('{}/{}'.format(URL['base'], link), cookies=cookies)

    bs = BeautifulSoup(r.content)

    try:
        trs = bs.find('table', id='tablaProds').find_all('tr')[1:]
    except:
        logger.error('Not table found in {}'.format(link))
        return bs

    logger.debug('found {} products'.format(len(trs)))

    for tr in trs:
        tds = tr.find_all('td')

        if len(tds) == 1:
            logger.debug('Empty page')
            return bs

        _id = list(tds[0].children)[0].get('onclick').rsplit('=', 1)[1][:-1]
        description = tds[2].text
        price_x = tds[4].text.split('$')[1].replace(',','.')
        price_unit = ''
        link = ''
        image = ''

        row = [description, price_x, _id, price_unit, link, image,
               category, date.today().isoformat()]

        urow = []
        for r in row:
            if isinstance(r, unicode):
                urow.append(r)
            else:
                urow.append(r.decode('utf-8'))

        try:
            csvwriter.writerow(urow)
        except UnicodeDecodeError:
            logger.error('Some of the columns in this '
                         'row are not Unicode compatible.')
    return bs


for category, link in menu:
    while link:
        logger.debug('getting: {}'.format(link))
        bs = scrap_page(category, link)
        try:
            link =  bs.find('div', id='Resultados').find_all('table')[1].find_all('input', {'value':'Siguiente'})[0].get('onclick').split('=',1)[1].strip()[1:-1]
        except:
            link = ''
fp.close()

