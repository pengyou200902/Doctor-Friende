# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from settings import begin, end


first = str(begin)
last = str(end - 1)


def get_number(url):
    return url.split(".")[-2].split("_")[-1]


def strip(s):
    return s.strip("\n|\r")


class MedicalSpiderPipeline(object):
    def process_item(self, item, spider):
        with open('./MedicalSpider/data/disease-' + first + '-' + last + '.json', 'a', encoding="UTF-8") as f:
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            f.write(line)
        return item


class NumberSpiderPipeline(object):
    def process_item(self, item, spider):
        hrefs = item["numbers"]
        numbers = '\r'.join(list(map(get_number, hrefs)))
        numbers += '\r'
        item["numbers"] = numbers
        # print(numbers)
        with open('./MedicalSpider/data/numbers.csv', 'a', encoding="UTF-8") as f:
            f.write(numbers)
        f.close()
        return item
