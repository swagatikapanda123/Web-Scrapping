import scrapy

class Dealers(scrapy.Spider):
    name = 'dealers'

    start_urls = [
        'https://www.cars.com/dealers/buy/77002/'
    ]

    def parse(self, response):
        for dealer in response.xpath("//div[@class='result-row']"):
            yield{
                'dealer-contact':dealer.xpath(".//h2[contains(@class, 'result-name')]/text()").extract_first()
            }

        next_page = response.xpath("//a[contains(@class, 'button next-page')]").extract_first()
        if next_page is not None:
            next_page_link = response.urljoin(next_page)
            yield scrapy.Request(url=next_page_link, callback=self.parse)

