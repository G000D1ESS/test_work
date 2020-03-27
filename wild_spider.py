import scrapy
import datetime;

class WildberriesSpider(scrapy.Spider):

    name = "wildberries_spider"
        
    def start_requests(self):

        # Start Searching from Category
        url = "https://www.wildberries.ru/catalog/pitanie/bakaleya/suhofrukty"
        
        yield scrapy.Request(url=url, callback=self.get_start_urls)

    def get_start_urls(self, response):

        # Get Resonse List of Products From [Main table]
        products = response.css('div.catalog_main_table a.ref_goods_n_p')

        # Adding new Main Page if it exists
        next_main_page = response.css('div.pager a.next::attr(href)').get()
        if next_main_page is not None:
            yield response.follow(next_main_page, callback=self.get_start_urls)

        # Parse Product Page
        yield from response.follow_all(products, callback=self.parse)
        
    def parse(self, response): 
        yield {
            'timestamp': int(datetime.datetime.now().timestamp()),
            'name': response.css('span.name::text').get(),
        }
