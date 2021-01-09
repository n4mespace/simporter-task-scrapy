import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from scrapy import Item
from scrapy.spiders import CrawlSpider, Rule
from scrapy_splash import SplashRequest

from typing import List, Tuple, Iterable, Optional, Dict

from ...items import MenHoodieItem, ReviewItem


class MenHoodiesSpider(CrawlSpider):
    name: str = "men_hoodies"
    allowed_domains: List[str] = ["www.dresslily.com"]
    start_urls: List[str] = [
        "https://www.dresslily.com/hoodies-c-181-page-1.html",
    ]

    rules: Tuple[Rule, ...] = (
        Rule(LinkExtractor(allow=r"page-[0-9]+")),
        Rule(
            LinkExtractor(allow=r"product[0-9]+"),
            callback="parse_item",
        ),
    )

    NAME_XPATH: str = "/html/body/div[1]/div[5]/div[3]/h1/span[2]/text()"
    DISCOUNT_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[3]/div[1]/div[1]/span[3]/span/text()"
    PRODUCT_INFO_KEYS_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[12]/div[2]/div[5]/div[1]/div//strong/text()"
    PRODUCT_INFO_VALUES_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[12]/div[2]/div[5]/div[1]/div/div[2]/div/text()"
    TOTAL_REVIEWS_XPATH: str = "//*[@id='js_reviewCountText']/text()"
    ORIGINAL_PRICE_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[3]/div[1]/div[1]/span[3]/span/text()"

    product_id_counter: int = 0

    def parse_item(self, response: HtmlResponse) -> Iterable[Item]:
        product_id: int = self.product_id_counter
        product_url: str = response.url
        name: Optional[str] = (
            response.xpath(self.NAME_XPATH).extract_first() or ""
        )

        original_price_str: Optional[str] = response.xpath(
            self.ORIGINAL_PRICE_XPATH
        ).extract_first()
        original_price: float = (
            float(original_price_str) if original_price_str else 0.0
        )

        discount_str: Optional[str] = response.xpath(
            self.DISCOUNT_XPATH
        ).extract_first()
        discount: int = int(discount_str) if discount_str else 0

        discounted_price: float = (
            original_price * discount / 100.0 if discount else 0.0
        )

        product_info_keys: List[str] = list(
            map(
                str.strip,
                response.xpath(self.PRODUCT_INFO_KEYS_XPATH).extract(),
            )
        )
        product_info_values: List[str] = list(
            map(
                str.strip,
                response.xpath(self.PRODUCT_INFO_VALUES_XPATH).extract(),
            )
        )[1::2]
        product_info: str = "".join(
            [
                f"{k}{v};"
                for (k, v) in zip(product_info_keys, product_info_values)
            ]
        )

        total_reviews_str: Optional[str] = response.xpath(
            self.TOTAL_REVIEWS_XPATH
        ).extract_first()
        total_reviews: int = int(total_reviews_str) if total_reviews_str else 0

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

        # yield ReviewItem()

    def _build_request(self, rule_index, link):
        return SplashRequest(
            url=link.url,
            callback=self._callback,
            errback=self._errback,
            endpoint="render.html",
            args={"wait": 15.0},
            meta=dict(rule=rule_index, link_text=link.text),
        )
