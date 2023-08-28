from datetime import datetime
import re
import sys

import scrapy

sys.path.append('../../')

from utils import float_number_clear

products_base_xpath = '//*[@id="products_grid"]/div/table/tbody/tr[*]/td/div/form/div[2]/div[1]'
product_name_xpath = f'{products_base_xpath}/h6/a/text()'
product_currency_xpath = f'{products_base_xpath}/div/span[1]/text()'
product_price_xpath = f'{products_base_xpath}/div/span[1]/span/text()'

next_page_xpath = '//*[@id="wrap"]/div[2]/div[5]/ul/li[9]/a/@href'

product_name_regex_pattern = r'kit(\w\s)? ((\d|,|\.)*(?=\s?kwp)).* - \s*(\w*)'

class SolplaceSpider(scrapy.Spider):

    name = 'solplace'

    start_urls = ['https://www.solplace.com.br/shop']

    def parse(self, response):
        updated_at = datetime.now()
        product_names = response.xpath(product_name_xpath).getall()
        product_prices = response.xpath(product_price_xpath).getall()

        products = list(zip(product_names, product_prices))

        for product in self.__products_list_parse(products):
            yield dict(**product, updated_at = updated_at)

        next_page = response.xpath(next_page_xpath).get()

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
