import scrapy
import time
from MedicalSpider.items import Disease, DiseaseTag
from settings import begin, end


start = begin
end = end


def strip(s):
    return s.strip('\n').strip('\r')


def unify(s):
    return s.replace('\r', '').replace(' ', '').replace('\t', '').replace('\n', '')\
            .replace('\xa0', '').replace('\u3000', '')


def read_numbers(start, end):
    with open('./MedicalSpider/data/numbers.csv', 'r', encoding="UTF-8") as f:
        numbers = f.readlines()[start:end]
        # numbers = f.readlines()[2500:3500]     # in order to split
        numbers = list(map(strip, numbers))
    f.close()
    print(numbers)
    print(len(numbers))
    return numbers


class MedicalSpider(scrapy.Spider):
    name = "medical"
    allowed_domains = ["jib.xywy.com"]
    # start_urls = [
    # http: // jib.xywy.com / il_sii_10136.htm
    # "http://jib.xywy.com/il_sii/gaishu/10136.htm",
    # "http://jib.xywy.com/il_sii/cause/10136.htm",
    # "http://jib.xywy.com/il_sii/prevent/10136.htm",
    # "http://jib.xywy.com/il_sii/neopathy/10136.htm",  # ------------No
    # "http://jib.xywy.com/il_sii/symptom/10136.htm",
    # "http://jib.xywy.com/il_sii/inspect/10136.htm",   # ------------No
    # "http://jib.xywy.com/il_sii/diagnosis/10136.htm", # ------------No
    # "http://jib.xywy.com/il_sii/treat/10136.htm",
    # "http://jib.xywy.com/il_sii/nursing/10136.htm",
    # "http://jib.xywy.com/il_sii/food/10136.htm"
    # "http://jib.xywy.com/il_sii/drug/10136.htm"
    # ]    # 1-10136
    custom_settings = {
        "ITEM_PIPELINES": {
            'MedicalSpider.pipelines.MedicalSpiderPipeline': 500,
        },
    }
    numbers = read_numbers(start, end)    # ['6978'] missing finally  # 参数是行数起止，并非数字起止
    failures = dict()

    def start_requests(self):
        for i in self.numbers:
            if int(i) % 15 == 0:
                t = 3.1415 * 3.141592
                print("Now reach i=%s and delay for %s sec" % (i,  t))
                time.sleep(t)
            else:
                print("Now reach i=%s" % i)
            url = "http://jib.xywy.com/il_sii/gaishu/%s.htm" % i
            disease = Disease()
            disease["id"] = i
            start_req = scrapy.Request(url, callback=self.parse, method="GET")
            start_req.meta["disease"] = disease
            yield start_req

    def parse(self, response):
        # print(response.text)
        # disease = response.meta["disease"]
        return self.parse_intro(response)

    def parse_intro(self, response):  # name,
        # print(response.text)
        disease = response.meta["disease"]
        disease_name = response.xpath('//div[@class="jib-articl-con jib-lh-articl"]//strong/text()').get()
        intro = response.xpath('//div[@class="jib-articl-con jib-lh-articl"]//p/text()').get()
        insurance = response.xpath('//span[contains(text(), "医保疾病")]/../span[2]/text()').get()
        get_prob = response.xpath('//span[contains(text(), "患病比例")]/../span[2]/text()').get()
        easy_get = response.xpath('//span[contains(text(), "易感人群")]/../span[2]/text()').get()
        get_way = response.xpath('//span[contains(text(), "传染方式")]/../span[2]/text()').get()
        neopathy = response.xpath('//span[contains(text(), "并发症")]/../span[2]/a/text()').getall()
        cure_dept = response.xpath('//span[contains(text(), "就诊科室")]/../span[2]/text()').get()
        treat = response.xpath('//span[contains(text(), "治疗方式")]/../span[2]/text()').get()
        treat_prob = response.xpath('//span[contains(text(), "治愈率")]/../span[2]/text()').get()
        treat_period = response.xpath('//span[contains(text(), "治疗周期")]/../span[2]/text()').get()
        drug = response.xpath('//span[contains(text(), "常用药品")]/../span[2]/a/text()').getall()
        treat_cost = response.xpath('//span[contains(text(), "治疗费用")]/../span[2]/text()').get()

        if disease_name:
            disease["name"] = disease_name.split("简介")[0]
        if intro:
            disease["intro"] = unify(intro)
        if insurance:
            disease["insurance"] = unify(insurance)
        if get_prob:
            disease["get_prob"] = unify(get_prob)
        if cure_dept:
            disease["cure_dept"] = unify(cure_dept)
        if easy_get:
            disease["easy_get"] = unify(easy_get)
        if get_way:
            disease["get_way"] = get_way
        # if cure_dept:
        #     disease["cure_dept"] = cure_dept
        if neopathy:
            disease["neopathy"] = [unify(n) for n in neopathy]
        if drug:
            disease["drug"] = drug
        if treat:
            disease["treat"] = treat
        if treat_prob:
            disease["treat_prob"] = treat_prob
        if treat_period:
            disease["treat_period"] = treat_period
        if treat_cost:
            disease["treat_cost"] = treat_cost
        # return disease
        next_url = "http://jib.xywy.com/il_sii/cause/" + disease["id"] + ".htm"
        next_req = scrapy.Request(next_url, callback=self.parse_cause, method="GET")
        next_req.meta["disease"] = disease
        yield next_req

    def parse_cause(self, response):
        disease = response.meta["disease"]
        infobox = []
        ps = response.xpath('//div[@class=" jib-articl fr f14 jib-lh-articl"]/p')
        for p in ps:  # 一段一段地拼接
            info = unify(p.xpath('string(.)').get())
            if info:
                infobox.append(info)
        disease["cause"] = '\n'.join(infobox)

        next_url = "http://jib.xywy.com/il_sii/prevent/" + disease["id"] + ".htm"
        next_req = scrapy.Request(next_url, callback=self.parse_prevent, method="GET")
        next_req.meta["disease"] = disease
        yield next_req

    def parse_prevent(self, response):
        disease = response.meta["disease"]
        prevent = []
        for p in response.xpath('string(//div[@class="jib-articl fr f14 jib-lh-articl"])').get().split('\n'):
            p = unify(p)
            if p:
                prevent.append(p)
        disease["prevent"] = '\n'.join(prevent)

        next_url = "http://jib.xywy.com/il_sii/symptom/" + disease["id"] + ".htm"
        next_req = scrapy.Request(next_url, callback=self.parse_symptom, method="GET")
        next_req.meta["disease"] = disease
        yield next_req

    def parse_symptom(self, response):
        disease = response.meta["disease"]
        symptom = []
        for s in response.xpath('//strong[contains(text(), "常见症状")]/../span/a/text()').getall():
            s = unify(s)
            if s:
                symptom.append(s)
        disease["symptom"] = symptom

        next_url = "http://jib.xywy.com/il_sii/treat/" + disease["id"] + ".htm"
        next_req = scrapy.Request(next_url, callback=self.parse_treat, method="GET")
        next_req.meta["disease"] = disease
        yield next_req

    # def parse_inspect(self, response):
    #     pass
    #
    # def parse_diagnosis(self, response):
    #     pass

    def parse_treat(self, response):
        disease = response.meta["disease"]
        treat_detail = []
        article = response.xpath('//div[@class="jib-lh-articl"]//./text()').getall()
        if article:
            for content in article:
                content = unify(content)
                if content:
                    if content == "：":
                        treat_detail[-1] += content
                    else:
                        treat_detail.append(content)
            treat_detail = '\n'.join(treat_detail)
        disease["treat_detail"] = treat_detail

        next_url = "http://jib.xywy.com/il_sii/nursing/" + disease["id"] + ".htm"
        next_req = scrapy.Request(next_url, callback=self.parse_nursing, method="GET")
        next_req.meta["disease"] = disease
        yield next_req

    def parse_nursing(self, response):
        disease = response.meta["disease"]
        nursing = []
        article = response.xpath('//strong[@class="db f20 fYaHei fb jib-articl-tit tc"]/../p/text()').getall()
        if article:
            for content in article:
                nursing.append(unify(content))
            nursing = '\n'.join(nursing)
        disease["nursing"] = nursing

        next_url = "http://jib.xywy.com/il_sii/food/" + disease["id"] + ".htm"
        next_req = scrapy.Request(next_url, callback=self.parse_food, method="GET")
        next_req.meta["disease"] = disease
        yield next_req

    def parse_food(self, response):
        disease = response.meta["disease"]
        article = response.xpath('//div[@class="diet-img clearfix mt20"]')
        if article:
            disease["can_eat"] = article[0].xpath('./div/p/text()').getall()
            disease["not_eat"] = article[1].xpath('./div/p/text()').getall()
        return disease

    # def is_failure(self, url, status):
    #     old = self.failures.get(url)
    #     if status == 200:
    #         return False
    #     else:
    #         if old:
    #             times = old['times']
    #         else:
    #             times = 1
    #         failure = {url: {'status': status, 'times': times}}
    #         self.failures.update(failure)
    #         print("Add failure----> " + str(failure))
    #         return True


class NumberSpider(scrapy.Spider):
    name = "keyword"
    allowed_domains = ["jib.xywy.com"]
    custom_settings = {
        "ITEM_PIPELINES": {
            "MedicalSpider.pipelines.KeyWordSpiderPipeline": 500
        },
    }

    def start_requests(self):
        for i in range(0, 26):
            url = "http://jib.xywy.com/html/%s.html" % chr(ord('a') + i)
            print(url)
            diseaseTag = DiseaseTag()
            start_req = scrapy.Request(url, callback=self.parse, method="GET")
            start_req.meta["diseaseTag"] = diseaseTag
            start_req.meta["idx"] = chr(ord('A') + i)
            yield start_req

    def parse(self, response):
        diseaseTag = response.meta["diseaseTag"]
        char = response.meta["idx"]
        diseaseTag["char"] = char
        # html = response.text    # <a href="/il_sii_10099.htm">病毒性感冒</a>
        xpath_char = ['A', char]
        href = []
        href += response.xpath("//div[@id='ill%c']//ul//li//a/@href" % xpath_char[0]).getall()
        href += response.xpath("//div[@id='ill%c']//ul//li//a/@href" % xpath_char[1]).getall()
        diseaseTag["numbers"] = href
        return diseaseTag


class ForumSpider(scrapy.Spider):
    name = "keyword"
    allowed_domains = ["jib.xywy.com"]
    custom_settings = {
        "ITEM_PIPELINES": {
            "MedicalSpider.pipelines.ForumSpiderPipeline": 500
        },
    }

    def start_requests(self):
        pass

    def parse(self, response):
        pass





