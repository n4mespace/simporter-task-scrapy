from scrapy import Item, Field


class MenHoodieItem(Item):
    product_id = Field()
    name = Field()
    product_url = Field()
    original_price = Field()
    discounted_price = Field()  # 0 if no sale
    discount = Field()  # In percents
    total_reviews = Field()
    product_info = (
        Field()
    )  # formatted string, e.g. “Occasion:Daily;Style:Fashion”


class ReviewItem(Item):
    product_id = Field()
    rating = Field()
    timestamp = Field()  # Unix timestamp
    text = Field()
    size = Field()
    color = Field()
