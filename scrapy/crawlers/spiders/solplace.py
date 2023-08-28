from datetime import datetime
import logging
import re

import scrapy

products_base_xpath = '//*[@id="products_grid"]/div/table/tbody/tr[*]/td/div/form/div[2]/div[1]'
product_name_xpath = f'{products_base_xpath}/h6/a/text()'
product_currency_xpath = f'{products_base_xpath}/div/span[1]/text()'
product_price_xpath = f'{products_base_xpath}/div/span[1]/span/text()'

next_page_xpath = '//*[@id="wrap"]/div[2]/div[5]/ul/li[9]/a/@href'

product_name_regex_pattern = r'kit(\s?\w+)* (([0-9]|,)+\s?kwp) -\s*(\w+)'

class SolplaceSpider(scrapy.Spider):

    name = 'solplace'

    start_urls = ['https://www.solplace.com.br/shop']

    def parse(self, response):
        updated_at = datetime.now()
        product_names = response.xpath(product_name_xpath).getall()
        product_currencies = response.xpath(product_currency_xpath).getall()
        product_prices = response.xpath(product_price_xpath).getall()

        products = list(zip(product_names, product_currencies, product_prices))

        for product in self.__products_list_parse(products):
            yield dict(**product, updated_at = updated_at)

        next_page = response.xpath(next_page_xpath).get()

        if next_page is not None:
            yield response.follow(next_page, callback = self.parse)

    def __products_list_parse(self, products):
        for name, currency, price in products:
            matches = re.match(product_name_regex_pattern, name.lower())

            if matches:
                port = matches.group(2)
                structure = matches.group(4)

            else:
                self.logger.warning(f'One of the listed products\' name didn\'t matched the expected pattern! Received name: {name}')
                continue

            yield {
                'port': port,
                'price': f'{currency}{price}',
                'structure': structure
            }
