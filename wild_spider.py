import scrapy
import datetime

class WildberriesSpider(scrapy.Spider):

    name = "wildberries_spider"
    uniq_id = 0
    
    """ First stage """
    def start_requests(self):

        # Start Searching from Category
        url = "https://www.wildberries.ru/catalog/pitanie/bakaleya/suhofrukty"
        
        yield scrapy.Request(url=url, callback=self.get_start_urls)

    """ Fill stack Products from Main Pages """
    def get_start_urls(self, response):

        # Get Resonse List of Products From [Main table]
        products = response.css('div.catalog_main_table a.ref_goods_n_p')

        # Adding new Main Page if it exists
        next_main_page = response.css('div.pager a.next::attr(href)').get()
        if next_main_page is not None:
            yield response.follow(next_main_page, callback=self.get_start_urls)

        # Parse Product Page
        yield from response.follow_all(products, callback=self.parse)

    """ Return product Price data from response """
    def get_price_data(self, response):

        # "price_data": {
        #         "current": 0.,  # {float}цена со скидкой, если скидки нет то = original
        #         "original": 0., # {float}оригинальная цена
        #         "sale_tag": None  #{str} если есть скидка на товар то формат: 'Скидка {}%'.format(discount)
        # }

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
        

        return {
            "current": current,     #   {float} цена со скидкой, если скидки нет то = original
            "original": original,   #   {float} оригинальная цена
            "sale_tag": sale_tag    #   {str}   если есть скидка на товар то формат: 'Скидка {}%'.format(discount)
        }
    
    """ Return Stock of product - USELESS """
    def get_stock(self, response):

        # USELESS FUNCTION - сайт не показывает товары, которых нет в налиии
          
        # "stock": {
        #      "in_stock": True, # {bool} должно отражать наличие товара в магазине
        #      "count": 0  # {int}это поле в случае наличия информации о количестве
        # }

        in_stock = response.css('div.final-price-block').get() != None

        if in_stock is True:
            count = 1
        else:
            count = 0

        return {
            "in_stock": in_stock,
            "count": count
        }

    """ Get Assets - Photo and Video Info """
    def get_asssets(self, response):
        
        # "assets": {
        #   "main_image": "", # {str}
        #   "set_images": [], # {str}список больших изображений товара
        #   "view360": [],
        #   "video": []
        # }

        set_image = response.css('#scrollImage li a.j-carousel-image::attr(href)').getall()

        # Проверка на наличие фото
        if set_image is not None:
            main_page = set_image[0]
        else:
            main_page = ""
        
        return {
            "main_image": main_page, 
            "set_image": set_image,
            "view360": [],
            "video": []
        }

    """ Get Metadata - Article, Size, Another info """
    def get_metadata(self, response):
        
        # "metadata": {
        #    "__description": # {str} Описание товар  ,
        #    # ниже добавить ключи которые могут быть
        #    # на странице такие как Артикул, Код товара, и  свойства если они есть
        #    # 'АРТИКУЛ': 'A88834'    
        # }

        return {}

    """ Main parser """
    def parse(self, response):

        # Making Main Info
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
            "stock": self.get_stock(response),
            "assets": self.get_asssets(response),
            "metadata": self.get_metadata(response),
        }

        # Change Uniq ID to Next value
        self.uniq_id += 1
