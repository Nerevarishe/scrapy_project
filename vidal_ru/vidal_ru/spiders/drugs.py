from scrapy import Spider

from mongoengine import connect
from ..models import DrugRecord

connect('vidal_ru', host='10.0.0.1')


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

    def parse_drug_page(self, response):
        drug = DrugRecord()
        drug.drug_name = self.create_drug_name(response.xpath('//*[@class="products-table-name"]/text()').getall())
        drug.atc_code = self.parse_string(response.xpath('//*[@id="atc_codes"]/span[2]/a/text()').get())
        drug.active_substances_rus = \
            self.create_list_of_components(
                response.xpath('//*[@id="composition"]/div/table/tr/td/text()[not(../../*[@colspan="2"])]').getall())
        # TODO: Выловить ошибку с NoneType первого элемента.
        drug.owners = self.parse_string(response.xpath('//*[@class="owners"]/a/text()').get()) + ' ' + \
                      self.parse_string(response.xpath('//*[@class="owners"]/span/text()').get())

        # TODO: Не записывать пустого дистрибутора в БД
        drug.distributor = self.create_distributor(response.xpath('//*[@class="distributor"]//text()').getall())

        drug.save()

    @staticmethod
    def parse_string(string: str) -> str:
        """
        Delete from string not needed spaces and symbols
        :param string: str
        :return: str
        """

        if string is not None:
            string = string.replace('\n', '')
            string = string.replace('\u2003', '')
            string = string.replace('\xad', '')
            string = string.lstrip()
            string = string.rstrip()
            return string

    def create_drug_name(self, data: list) -> str:
        """
        Create drug name from list of strings
        :param data:
        :return:
        """
        new_data = []
        for item in data:
            item = self.parse_string(item)
            if item != '':
                new_data.append(item)

        return ' '.join(new_data)

    def create_list_of_components(self, iterable: list) -> list:
        if iterable is not None:
            key = []
            value = []
            cnt = 1
            for item in iterable:
                if (cnt % 2) != 0:
                    key.append(self.parse_string(item))
                    cnt += 1
                else:
                    value.append(self.parse_string(item))
                    cnt = 1
            return list(zip(key, value))

    def create_distributor(self, iterable: list) -> str:
        distributor = []
        for item in iterable:
            data = self.parse_string(item)
            if data is not '' or None:
                distributor.append(data)
        return ' '.join(distributor[1:])
