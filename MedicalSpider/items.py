# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DiseaseTag(scrapy.Item):
    char = scrapy.Field()
    numbers = scrapy.Field()


class Disease(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()
    category = scrapy.Field()
    intro = scrapy.Field()
    cause = scrapy.Field()
    easy_get = scrapy.Field()
    get_by = scrapy.Field()
    check = scrapy.Field()
    symptom = scrapy.Field()
    neopathy = scrapy.Field()
    prevent = scrapy.Field()
    cure_dept = scrapy.Field()
    treat = scrapy.Field()
    treat_detail = scrapy.Field()
    treat_prob = scrapy.Field()
    treat_period = scrapy.Field()
    drug = scrapy.Field()
    nursing = scrapy.Field()
    get_prob = scrapy.Field()
    get_way = scrapy.Field()
    treat_cost = scrapy.Field()
    insurance = scrapy.Field()
    can_eat = scrapy.Field()
    not_eat = scrapy.Field()

