# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from hashlib import sha256
import json
import sys

sys.path.append('..')

from dao.dao import MysqlConnection

class CrawlersPipeline:

    def __init__(self):
        self.items = []

    def process_item(self, item, spider):
        origin = spider.name
        portage = item.get('portage', '')
        structure = item.get('structure', '')
        product_id = item.get('product_id', '')

        if 'product_id' in item:
            del item['product_id']

        sha_input = ''.join([
            origin, str(portage), structure, str(product_id)
        ])

        item['sha_id'] = sha256(sha_input.encode('utf-8')).hexdigest()
        item['origin'] = origin
        item['updated_at'] = item['updated_at'].isoformat()

        self.items.append(item)
        return item

    def close_spider(self, spider):
        if len(self.items) == 0:
            print('No items to be written')

        else:
            connection = MysqlConnection(
                'root', 'greener_case',
                'mysql', 'landing_db'
            )

            connection.upsert_statement('solar_panels', *self.items)

            del connection
