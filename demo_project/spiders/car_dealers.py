import scrapy
from scrapy.http import headers

class CarDealersSpider (scrapy.Spider):
    name = "car_dealers"

    def start_requests(self):

        zip_codes = ['77001', '66006']

        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
        }
        for zip_code in zip_codes:
                url = 'https://www.cars.com/dealers/buy/' + zip_code + \
                    '/?rd=30&sortBy=DISTANCE&order=ASC&perPage=200'
                yield scrapy.Request(url=url, callback=self.parse_listings_page, headers=headers)

    def parse_listings_page(self, response):
        # get each individual dealer section
        dealers = response.xpath('//*[@class="dealer-result"]')

        for dealer in dealers:
            #extracting the name for every dealer
            name = dealer.xpath('.//h2[contains(@class, "result-name")]/text()').extract_first().strip()
            # extract the stars
            stars = dealer.xpath('.//div[@itemprop="aggregateRating"]//*[contains(@class, "icon-image")]/@class').extract()
            star_rating = 0

            for star in stars:
                if 'filled' in star:
                    star_rating += 1
                elif 'half' in star:
                    star_rating += 0.5
            
            address = dealer.xpath('.//address/div[1]/span[not(@class = "distance)]/text()').extract()
            # list comprehension
            address = [a.replace("\n", "").strip() for a in address]
            # after cleaning join each part(street address, city and pincode) in address 

            review_count = dealer.xpath('.//a[@class="reviews-link"]/text()').extract_first()
            review_count = review_count.replace(" reviews", "").replace(" review", "").replace("\n", "").strip()
            review_count = review_count.replace(" recent", "")
            review_count = 0 if review_count == "no" else int(review_count)

            # we create a new object that we will pass to the next request
            dealer_obj = {
                'name' : name,
                'ratying' : star_rating,
                'number_of_review' : review_count,
                'address' : address,
                'used_phone': '',
                'new_phone': '',
                'service_phone': ''
            }

            phone_numbers = dealer.xpath('.//table[@class="sales-phone-numbers"]/tr')
            for number in phone_numbers:
                phone_type = number.xpath('.//td[@class="phone-number-label"]/text()').extract_first().strip()
                number_xpath = './/td[@class="phone-number-value"]/a[@class="clickable-phone-number"]/text()'
                phone_number = number.xpath(number_xpath).extract_first()

                if not phone_numbers:
                    continue

                phone_numbers = phone_numbers.replace("\n", "").strip()

                if phone_type == "New":
                    dealer_obj['new_phone'] = phone_number
                if phone_type == "Used":
                    dealer_obj['used_phone'] = phone_number
                if phone_type == 'Service':
                    dealer_obj['service_phone'] = phone_number

            # getting the url of the specific page of the dealer
            dealer_url = dealer.xpath('.//a[@data-linkname="dealer-name"]/@href').extract_first()
            dealer_url = 'https://www.cars.com' + dealer_url

            # pass the url to new request
            yield scrapy.Request(url=dealer_url, headers=self.headers, callback=self.parse_dealer_page, meta={'dealer': dealer_obj})

    def parse_dealer_page(self, response):
        dealer = response.meta['dealer']
        dealer['listing_url'] = response.request.url

        # get dealer's website
        website = response.xpath('//a[@class="dealer-update-website-link"]/@href').extract_first()
        dealer['website'] = website

        vehicle_count_new = response.xpath('//dpp-update-inventory-link/@new-count').extract_first()
        vehicle_count_used = response.xpath('//dpp-update-inventory-link/@used-count').extract_first()

        vehicle_count_new = vehicle_count_new if vehicle_count_new else 0
        vehicle_count_used = vehicle_count_used if vehicle_count_used else 0

        vehicle_count = int(vehicle_count_new) + int(vehicle_count_used)

        # We define all the vehice counts
        dealer['vehicle_count_total'] = vehicle_count
        dealer['vehicle_count_used'] = vehicle_count_used
        dealer['vehicle_count_new'] = vehicle_count_new

        # finally yeild the values to be stored in database in JSON or csv format
        yield dealer
