import os
from settings import begin, end

first = str(begin)
last = str(end - 1)
# cmd = "scrapy crawl " + "keyword"
cmd = "scrapy crawl " + "medical -s JOBDIR=" + './jobs/medical-' + first + '-' + last
os.system(cmd)


# from MedicalSpider.spiders.MedicalSpider import read_numbers
# read_numbers()
