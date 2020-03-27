import scrapy
import datetime

class WildberriesSpider(scrapy.Spider):

    name = "wildberries_spider"
    uniq_id = 0
        
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

    def get_price_data(self, response):

        # Check to Sale
        if response.css('span.old-price').get() is not None:
            
            # Cleaning to right convert [str -> float]
            cur_txt = response.css('span.final-cost::text').get().replace('\xa0', ' ').replace('₽', ' ').replace(' ', '')
            current = float(cur_txt.strip())

            # Cleaning to right convert [str -> float]
            org_txt  = response.css('span.old-price del.c-text-base::text').get().replace('\xa0', ' ').replace('₽', ' ').replace(' ', '')
            original = float(org_txt.strip())

            # Sale [int]
            discount = 100 - int((current/original)*100)

            sale_tag = 'Сидка {}%'.format(discount)
        else:
            
            # Cleaning to right convert [str -> float]
            cur_txt = response.css('span.final-cost::text').get().replace('\xa0', ' ').replace('₽', ' ').replace(' ', '')
            current = float(cur_txt.strip())

            # No Sale
            original = current

            sale_tag = 'Скидки нет'


        price_data = {
            "current": current,     #   {float} цена со скидкой, если скидки нет то = original
            "original": original,   #   {float} оригинальная цена
            "sale_tag": sale_tag    #   {str}   если есть скидка на товар то формат: 'Скидка {}%'.format(discount)
        }
        
        return price_data
        
    def parse(self, response):

        yield {
            "timestamp": int(datetime.datetime.now().timestamp()),
            "name": response.css('span.name::text').get(),          # текущее время в формате timestamp,
            "RPC": self.uniq_id,                                    # {int} Уникальный код товара
            "url": response.url,                                    # {str} ссылка на страницу товара
            "title": response.css('title::text').get().strip(),     # {str} заголовок
            "marketing_tags": response.css('ul.tags-group-list li.tags-group-item a::text').getall(),
            "brand": response.css('span.brand::text').get(),        # {str} Брэнд товара
            "section": response.css('ul.bread-crumbs span::text').getall(), # {list str} Хлебные крошки, например: ['Игрушки','Развивающие и интерактивные игрушки','Интерактивные игрушки']
            
            "price_data": self.get_price_data(response),

        }
        self.uniq_id += 1
