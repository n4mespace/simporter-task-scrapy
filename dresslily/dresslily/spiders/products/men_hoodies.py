import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from scrapy import Item
from scrapy.spiders import CrawlSpider, Rule

from typing import List, Tuple, Iterable, Optional, Dict

from ...items import MenHoodieItem, ReviewItem


class MenHoodiesSpider(CrawlSpider):
    name: str = "men_hoodies"
    allowed_domains: List[str] = ["www.dresslily.com"]
    start_urls: List[str] = [
        "https://www.dresslily.com/hoodies-c-181-page-1.html",
    ]

    rules: Tuple[Rule, ...] = (
        Rule(
            LinkExtractor(allow=r"page-[0-9]+"),
        ),
        Rule(
            LinkExtractor(allow=r"product[0-9]+"),
            callback="parse_item",
        ),
    )

    NAME_XPATH: str = "/html/body/div[1]/div[5]/div[3]/h1/span[2]/text()"
    DISCOUNT_XPATH: str = ""
    PRODUCT_INFO_VALUES_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[12]/div[2]/div[5]/div[1]/div/div[2]/div/text()"
    TOTAL_REVIEWS_XPATH: str = "//*[@id='js_reviewCountText']/text()"

    PRODUCT_INFO_KEYS: List[str] = [
        "Clothes Type",
        "Occasion",
        "Style",
        "Fit Type",
        "Sleeve Length",
        "Material",
        "Thickness",
        "Patterns",
        "Season",
        "Weight",
        "Package Contents",
    ]

    product_id_counter: int = 0

    def parse_item(self, response: HtmlResponse) -> Iterable[Item]:
        product_id: int = self.product_id_counter
        product_url: str = response.url
        name: Optional[str] = response.xpath(self.NAME_XPATH).extract_first()
        original_price: Optional[float] = float()
        discount: Optional[int] = response.xpath(
            self.DISCOUNT_XPATH
        ).extract_first()
        discounted_price: float = (
            0.0 if not discount else original_price * discount / 100.0
        )
        product_info_values: List[str] = list(
            map(
                str.strip,
                response.xpath(self.PRODUCT_INFO_VALUES_XPATH).extract(),
            )
        )[1::2]
        product_info: Dict[str, str] = dict(
            zip(self.PRODUCT_INFO_KEYS, product_info_values)
        )

        total_reviews: Optional[int] = int(
            response.xpath(self.TOTAL_REVIEWS_XPATH).extract_first()
        )

        self.product_id_counter += 1

        yield MenHoodieItem(
            product_id=product_id,
            product_url=product_url,
            name=name,
            discount=discount,
            discounted_price=discounted_price,
            original_price=original_price,
            total_reviews=total_reviews,
            product_info=product_info,
        )

        yield ReviewItem()
