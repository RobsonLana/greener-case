from datetime import datetime
import re
import sys

import scrapy

sys.path.append('../../')

from utils import float_number_clear

products_base_selector = '#products_grid > div > table > tbody > tr > td > div > form > div.card-body.rounded-bottom.p-0.o_wsale_product_information > div.p-2.o_wsale_product_information_text'

product_name_selector = f'{products_base_selector} > h6 > a::text'
product_price_selector = f'{products_base_selector} > div > span > span::text'

next_page_selector = '#wrap > div.container.oe_website_sale > div.products_pager.form-inline.justify-content-center.py-3 > ul > li:last-child > a::attr(href)'

product_name_regex_pattern = r'kit (\w*\s)?((\d|,|\.)+(?=\s?kwp)).* -\s+(\S*)'

class SolplaceSpider(scrapy.Spider):

    name = 'solplace'

    start_urls = ['https://www.solplace.com.br/shop']

    def parse(self, response):
        updated_at = datetime.now()
        product_names = response.css(product_name_selector).getall()
        product_prices = response.css(product_price_selector).getall()

        products = list(zip(product_names, product_prices))

        for product in self.__products_list_parse(products):
            yield dict(**product, updated_at = updated_at)

        next_page = response.css(next_page_selector).get()

        if next_page is not None:
            yield response.follow(next_page, callback = self.parse)

    def __products_list_parse(self, products):
        for name, price in products:
            self.logger.info(name)
            matches = re.match(product_name_regex_pattern, name.lower())

            if matches:
                portage = matches.group(2)
                structure = matches.group(4)

            else:
                self.logger.warning(f'One of the listed products\' name didn\'t matched the expected pattern! Received name: {name}')
                continue

            yield {
                'portage': float(float_number_clear(portage)),
                'price': float(float_number_clear(price)),
                'structure': structure
            }
