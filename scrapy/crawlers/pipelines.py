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
from dao.validations import validate, schemas

class CrawlersPipeline:

    def __init__(self):
        self.items = []

    def process_item(self, item, spider):
        try:
            # validate(schemas['solar_panels'], item)
            origin = spider.name
            port = item.get('port', '')
            structure = item.get('structure', '')

            sha_input = '-'.join([origin, port, structure])

            item['sha_id'] = sha256(sha_input.encode('utf-8')).hexdigest()
            item['origin'] = origin
            item['updated_at'] = item['updated_at'].isoformat()

            self.items.append(item)
            return item

        except Exception as e:
            raise DropItem(f'One item from {spider.name} didn\'t passed the validation: {json.dumps(item, indent = 2)}')


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
