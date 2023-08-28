from datetime import datetime
import json
import re
import sys

import scrapy
from scrapy.http import JsonRequest
from scrapy.exceptions import CloseSpider
from scrapy.spidermiddlewares.httperror import HttpError

sys.path.append('../../')

from utils import float_number_clear

aldo_api_base_url = 'https://www.aldo.com.br/wcf/Produto.svc'

product_name_regex_pattern = r'\w*\s+(([0-9]|,|\.)*(?=kwp))'

# Para fins de demonstração, o crawler irá parar após coletar 30 páginas
pagination_hard_limit = 30

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
                errback = self.error_callback
            )
        ]

    def error_callback(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

            raise CloseSpider(f'Received HTTP Statuscode {response.url}')

    def parse(self, filter_response):
        self.logger.info(filter_response)
        body = json.loads(filter_response.text)
        filter_id = body['FilterId']

        products_url  = f'{aldo_api_base_url}/getprodutosporsegmentonotlogin'

        products_request_body = {
            'filterId': filter_id,
            'orderby': "2",
            'offset': 1
        }

        yield JsonRequest(
            url = products_url,
            method = 'POST',
            body = json.dumps(products_request_body),
            callback = self.__filtered_parse,
            meta = { 'offset': 1 }
        )

    def __filtered_parse(self, response):
        if response.status != 200:
            raise CloseSpider(f'Received HTTP Statuscode {response.url}')

        current_offset = response.meta.get('offset')

        if current_offset >= pagination_hard_limit:
            raise CloseSpider(f'Reached pagination limit ({pagination_hard_limit})')

        updated_at = datetime.now()

        self.logger.info(response.request.body)

        products = json.loads(response.text)
        products_request_body = json.loads(response.request.body)
        products_request_body['offset'] = current_offset + 1

        for product in products:
            name = product['prd_descricao']
            price = product['prd_preco']
            product_id = product['produto_id']

            matches = re.match(product_name_regex_pattern, name.lower())

            if matches:
                portage = matches.group(1)

            else:
                self.logger.warning(f'One of the listed products\' name didn\'t matched the expected pattern! Received name: {name}')
                continue

            yield {
                'portage': float(float_number_clear(portage)),
                'price': price,
                'updated_at': updated_at,
                'product_id': product_id
            }

        yield JsonRequest(
            url = response.url,
            method = 'POST',
            body = json.dumps(products_request_body),
            callback = self.__filtered_parse,
            meta = { 'offset': current_offset + 1 }
        )
