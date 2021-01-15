from scrapy import Item, Request as ScrapyRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from scrapy.spiders import Rule

from time import mktime
from datetime import datetime

from typing import List, Tuple, Iterable, Dict, Any, Union

from ...items import MenHoodieItem, ReviewItem
from ..splash_spider import SplashCrawlSpider


class MenHoodiesSpider(SplashCrawlSpider):
    name: str = "men_hoodies"

    allowed_domains: List[str] = ["www.dresslily.com"]
    start_urls: List[str] = [
        "https://www.dresslily.com/hoodies-c-181-page-1.html",
    ]
    item_reviews_page_url: str = "https://www.dresslily.com/m-review-a-view_review-goods_id-{product_id}-page-{page_num}.html"

    rules: Tuple[Rule, ...] = (
        Rule(
            LinkExtractor(allow=r"page-[0-9]+"),
        ),
        Rule(
            LinkExtractor(allow=r"product[0-9]+"),
            callback="parse_hoodie",
        ),
    )

    splash_args: Dict[str, Any] = {
        "wait": 3.0,
        "images": 0,
    }

    # Hoodie selectors
    NAME_XPATH: str = "//h1/span[@class='goodtitle']/text()"
    DISCOUNT_CSS: str = "span.off.js-dl-cutoff > span ::text"
    INFO_KEYS_XPATH: str = "//div[@class='xxkkk']/div//strong/text()"
    INFO_VALUES_XPATH: str = "//div[@class='xxkkk20']/text()"
    TOTAL_REVIEWS_XPATH: str = "//*[@id='js_reviewCountText']/text()"
    ORIGINAL_PRICE_WITHOUT_DISCOUNT_CSS: str = (
        "span.curPrice.my-shop-price.js-dl-curPrice ::attr(data-orgp)"
    )
    ORIGINAL_PRICE_WITH_DISCOUNT_CSS: str = "span.js-dl-marketPrice.marketPrice.my-shop-price.dl-has-rrp-tag > span.dl-price ::text"

    # Hoodie reviews selectors
    REVIEWS_LIST_XPATH: str = "//div[@class='reviewinfo']"
    RATING_SELECTED_STARS_XPATH: str = (
        ".//p[@class='starscon_b dib']/i[@class='icon-star-black']"
    )
    TIMESTAMP_XPATH: str = ".//span[@class='reviewtime']/text()"
    TEXT_XPATH: str = ".//p[@class='reviewcon']/text()"
    SIZE_XPATH: str = ".//p[@class='color-size']/span[1]/text()"
    COLOR_XPATH: str = ".//p[@class='color-size']/span[2]/text()"

    TIMESTAMP_FORMAT: str = "%b,%d %Y %H:%M:%S"
    REVIEWS_BY_PAGE_COUNT: int = 6

    def parse_hoodie(
        self, response: HtmlResponse
    ) -> Union[Iterable[Item], Iterable[ScrapyRequest]]:
        product_url: str = response.meta["real_url"]
        product_id: int = int(
            product_url.split("product")[-1].replace(".html", "")
        )
        name: str = response.xpath(self.NAME_XPATH).get("")
        original_price: float = float(
            response.css(self.ORIGINAL_PRICE_WITHOUT_DISCOUNT_CSS).get(0.0)
        )
        discounted_price: float = 0.0
        discount: int = int(response.css(self.DISCOUNT_CSS).get(0))

        if discount:
            discounted_price = original_price
            original_price = float(
                response.css(self.ORIGINAL_PRICE_WITH_DISCOUNT_CSS).getall()[
                    -1
                ]
            )

        product_info_keys: List[str] = response.xpath(
            self.INFO_KEYS_XPATH
        ).getall()

        product_info_values: List[str] = response.xpath(
            self.INFO_VALUES_XPATH
        ).getall()[1::2]

        product_info: str = "".join(
            [
                f"{k.strip()}{v.strip()};"
                for (k, v) in zip(product_info_keys, product_info_values)
            ]
        )

        total_reviews: int = int(
            response.xpath(self.TOTAL_REVIEWS_XPATH).get(0)
        )

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

        if total_reviews > 0:
            yield from self.parse_reviews_pages(
                product_id=product_id,
                total_reviews=total_reviews,
            )

    def parse_reviews_pages(
        self, product_id: int, total_reviews: int
    ) -> Iterable[ScrapyRequest]:
        reviews_left: int = total_reviews
        page_num: int = 1

        while reviews_left > 0:
            # No need in loading js
            yield ScrapyRequest(
                url=self.item_reviews_page_url.format(
                    product_id=product_id,
                    page_num=page_num,
                ),
                callback=self.parse_reviews,
                cb_kwargs={"product_id": product_id},
            )
            reviews_left -= self.REVIEWS_BY_PAGE_COUNT
            page_num += 1

    def parse_reviews(
        self, response: HtmlResponse, product_id: int
    ) -> Iterable[Item]:
        reviews: List[HtmlResponse] = response.xpath(self.REVIEWS_LIST_XPATH)

        for review in reviews:
            rating: int = len(
                review.xpath(self.RATING_SELECTED_STARS_XPATH).getall()
            )
            time: str = review.xpath(self.TIMESTAMP_XPATH).get("")
            timestamp: float = (
                mktime(
                    datetime.strptime(time, self.TIMESTAMP_FORMAT).timetuple()
                )
                if time
                else 0.0
            )
            text: str = review.xpath(self.TEXT_XPATH).get("")
            size: str = review.xpath(self.SIZE_XPATH).get(": ").split(": ")[-1]
            color: str = (
                review.xpath(self.COLOR_XPATH).get(": ").split(": ")[-1]
            )

            yield ReviewItem(
                product_id=product_id,
                rating=rating,
                timestamp=timestamp,
                text=text,
                size=size,
                color=color,
            )
