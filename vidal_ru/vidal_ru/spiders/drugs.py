from scrapy import Spider

from mongoengine import connect
from models import DrugRecord

connect('vidal_ru', host='10.0.0.1')


def parse_string(string):
    if string is not None:
        string = string.replace('\n', '')
        string = string.replace('\u2003', '')
        string = string.replace('\xad', '')
        string = string.lstrip()
        string = string.rstrip()
        return string


def create_list(iterable):
    if iterable is not None:
        key = []
        value = []
        cnt = 1
        for item in iterable:
            if (cnt % 2) != 0:
                key.append(parse_string(item))
                cnt += 1
            else:
                value.append(parse_string(item))
                cnt = 1
        return list(zip(key, value))


class Drugs(Spider):
    name = 'drugs'

    start_urls = [
        'https://www.vidal.ru'
    ]

    def parse(self, response):
        abc_urls = response.xpath('//div[@class="letters-russian"]/a/@href').getall()

        for url in abc_urls:
            yield response.follow(url, callback=self.open_letter_page)

    def open_letter_page(self, response):
        drugs_page_urls = response.xpath('//td[@class="products-table-name"]/a/@href').getall()
        for url in drugs_page_urls:
            yield response.follow(url, callback=self.parse_drug_page)
        next_letter_page = response.xpath('//*[@id="vidal"]/div/div/span[@class="next"]/a/@href').get()
        if next_letter_page is not None:
            yield response.follow(next_letter_page, callback=self.open_letter_page)

    @staticmethod
    def parse_drug_page(response):
        drug = DrugRecord()
        drug.drug_name = parse_string(response.xpath('//td[@class="products-table-name"]/text()').get())
        drug.atc_code = parse_string(response.xpath('//*[@id="atc_codes"]/span[2]/a/text()').get())
        drug.active_substances_rus = \
            create_list(response.xpath('//*[@id="composition"]/div/table/tr/td/text()[not(../../*[@colspan="2"])]')
                        .getall())
        drug.owners = parse_string(response.xpath('//*[@class="owners"]/a/text()').get()) + ' ' +\
                 parse_string(response.xpath('//*[@class="owners"]/span/text()').get())

        distributor = []
        for item in response.xpath('//*[@class="distributor"]//text()').getall():
            data = parse_string(item)
            if data is not '' or None:
                distributor.append(data)
        drug.distributor = ' '.join(distributor[1:])

        # drug.save()
