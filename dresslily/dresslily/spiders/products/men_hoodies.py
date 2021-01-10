import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from scrapy import Item
from scrapy.spiders import CrawlSpider, Rule
from scrapy_splash import SplashRequest, SplashTextResponse

from time import mktime
from datetime import datetime

from typing import List, Tuple, Iterable, Optional, Dict, Any

from ...items import MenHoodieItem, ReviewItem


lua_script_page_load: str = """
    function main(splash)
        assert(splash:go(splash.args.url))
        assert(splash:wait(1))

        while not splash:select('body > div.dl-page > div.good-main > div.good-hgap.good-basic-info > div.goodprice > div.goodprice-line > div.goodprice-line-start > span.curPrice.my-shop-price.js-dl-curPrice.shop-price-red > span') do
            assert(splash:wait(0.1))
        end

        return {
            html=splash:html()
        }
    end
"""


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

    splash_args: Dict[str, Any] = {
        "wait": 3.0,
        "png": 0,
        "html": 1,
        "endpoint": "execute",
        "lua_source": lua_script_page_load,
    }

    # Hoodie selectors
    NAME_XPATH: str = "/html/body/div[1]/div[5]/div[3]/h1/span[2]/text()"
    DISCOUNT_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[3]/div[1]/div[1]/span[3]/span/text()"
    INFO_KEYS_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[12]/div[2]/div[5]/div[1]/div//strong/text()"
    INFO_VALUES_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[12]/div[2]/div[5]/div[1]/div/div[2]/div/text()"
    TOTAL_REVIEWS_XPATH: str = "//*[@id='js_reviewCountText']/text()"
    ORIGINAL_PRICE_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[3]/div[1]/div[1]/span[3]/span/text()"

    # Hoodie review selectors
    REVIEWS_XPATH: str = (
        "/html/body/div[1]/div[5]/div[5]/div[4]/div[2]/div/div"
    )
    RATING_SELECTED_STARS_XPATH: str = (
        ".//p[@class='starscon_b dib']/i[@class='icon-star-black']"
    )
    TIMESTAMP_XPATH: str = ".//span[@class='reviewtime']/text()"
    TIMESTAMP_FORMAT: str = "%b,%d %Y %H:%M:%S"
    TEXT_XPATH: str = ".//p[@class='reviewcon']/text()"
    SIZE_XPATH: str = ".//p[@class='color-size']/span[1]/text()"
    COLOR_XPATH: str = ".//p[@class='color-size']/span[2]/text()"

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
                response.xpath(self.INFO_KEYS_XPATH).extract(),
            )
        )
        product_info_values: List[str] = list(
            map(
                str.strip,
                response.xpath(self.INFO_VALUES_XPATH).extract(),
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

        reviews: List[HtmlResponse] = response.xpath(self.REVIEWS_XPATH)[:-1]

        for review in reviews:
            rating: int = len(
                review.xpath(self.RATING_SELECTED_STARS_XPATH).extract()
            )
            time: str = review.xpath(self.TIMESTAMP_XPATH).extract_first()
            timestamp: float = mktime(
                datetime.strptime(time, self.TIMESTAMP_FORMAT).timetuple()
            )
            text: str = review.xpath(self.TEXT_XPATH).extract_first()
            size: str = (
                review.xpath(self.SIZE_XPATH).extract_first().split(": ")[-1]
            )
            color: str = (
                review.xpath(self.COLOR_XPATH).extract_first().split(": ")[-1]
            )

            yield ReviewItem(
                product_id=product_id,
                rating=rating,
                timestamp=timestamp,
                text=text,
                size=size,
                color=color,
            )

    # Replace scrapy Request to splash Request
    # details: https://github.com/scrapy-plugins/scrapy-splash/issues/92
    def _build_request(self, rule_index, link):
        return SplashRequest(
            url=link.url,
            callback=self._callback,
            endpoint="execute",
            # dont_process_response=True,
            errback=self._errback,
            args=self.splash_args,
            meta=dict(rule=rule_index, link_text=link.text),
        )

    # Add SplashTextResponse to instance check for follow ups to work
    # details: https://github.com/scrapy-plugins/scrapy-splash/issues/92
    def _requests_to_follow(self, response):
        if not isinstance(response, (HtmlResponse, SplashTextResponse)):
            return
        seen = set()
        for rule_index, rule in enumerate(self._rules):
            links = [
                lnk
                for lnk in rule.link_extractor.extract_links(response)
                if lnk not in seen
            ]
            for link in rule.process_links(links):
                seen.add(link)
                request = self._build_request(rule_index, link)
                yield rule.process_request(request, response)
