from datetime import datetime
import http.client
import json
import logging
import re
import requests
import scrapy
from scrapy.http import JsonRequest
from scrapy.spidermiddlewares.httperror import HttpError

aldo_api_base_url = 'https://www.aldo.com.br/wcf/Produto.svc'

product_name_regex_pattern = r'gf (([0-9]|,|\.)+\s?kwp)'

class AldoSpider(scrapy.Spider):
    name = 'aldo'

    def start_requests(self):
        filter_request_body = {
            'slug': 'energia-solar',
            'origem': 'categoria'
        }

        filter_url = f'{aldo_api_base_url}/getfiltrosporsegmento'

        return [
            JsonRequest(
                url = filter_url,
                method = 'POST',
                body = json.dumps(filter_request_body),
                callback = self.parse,
                errback = self.error_callback,
                meta = { 'proxy': '10.244.62.184:80' }
            )
        ]

    def error_callback(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

    def parse(self, filter_response):
        self.logger.info(filter_response)
        body = json.loads(filter_response.text)
        filter_id = body['FilterId']

        products_url  = f'{aldo_api_base_url}/getprodutosporsegmentonotlogin'

        products_request_body = {
            'filterId': filter_id,
            'orderby': "2"
        }

        offset_counter = 1
        self.minimum_pages_threshold = 10

        self.gateway_time_out_counter = 0
        self.gateway_time_out_tolerance = 10
        offset_end = False

        while not offset_end:
            products_request_body['offset'] = offset_counter

            updated_at = datetime.now()
            page_products = JsonRequest(
                url = products_url,
                method = 'POST',
                body = json.dumps(products_request_body),
                callback = self.__filtered_parse,
                meta = {
                    'updated_at': datetime.now()
                }
            )

            if page_products is not None:
                yield page_products

            offset_end = page_products == None
            offset_counter += 1

    def __filtered_parse(self, response):
        updated_at = response.meta.get('updated_at')

        self.gateway_time_out_tolerance += int(response.status == 504)

        if self.offset_counter > self.minimum_pages_threshold \
                and self.gateway_time_out_counter >= self.gateway_time_out_tolerance:
            self.logger.warning('Received 10 times the status code 504 (Gateway Timeout) after scrapped 10 pages, Giving up on task.')
            return None

        products = json.loads(response.text)

        if len(products) == 0:
            return None

        for product in products:
            name = product['prd_descricao']
            price = product['prd_preco']

            matches = re.match(product_name_regex_pattern, name.lower())

            if matches:
                port = matches.group(1)

            else:
                logging.warning(f'One of the listed products\' name didn\'t matched the expected pattern! Received name: {name}')
                continue

            yield {
                'port': port,
                'price': str(price),
                'updated_at': updated_at
            }
