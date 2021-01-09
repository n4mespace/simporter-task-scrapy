import scrapy


class MenHoodieItem(scrapy.Item):
    product_id = scrapy.Field()
    product_url = scrapy.Field()
    name = scrapy.Field()
    discount = scrapy.Field()  # In percents
    discounted_price = scrapy.Field()  # 0 if no sale
    original_price = scrapy.Field()
    total_reviews = scrapy.Field()
    product_info = (
        scrapy.Field()
    )  # formatted string, e.g. “Occasion:Daily;Style:Fashion”


class ReviewItem(scrapy.Item):
    product_id = scrapy.Field()
    rating = scrapy.Field()
    timestamp = scrapy.Field()  # Unix timestamp
    text = scrapy.Field()
    size = scrapy.Field()
    color = scrapy.Field()
