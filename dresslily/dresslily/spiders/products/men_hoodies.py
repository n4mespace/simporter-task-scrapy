from scrapy import Item
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from scrapy.spiders import CrawlSpider, Rule
from scrapy_splash import SplashRequest

from shutil import which
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options

from time import mktime
from datetime import datetime

from typing import List, Tuple, Iterable, Optional, Dict, Any, Union

from ...items import MenHoodieItem, ReviewItem
from ..splash_scripts import PAGE_LOADING_WAIT_SCRIPT


class MenHoodiesSpider(CrawlSpider):
    name: str = "men_hoodies"
    allowed_domains: List[str] = ["www.dresslily.com"]
    start_urls: List[str] = [
        "https://www.dresslily.com/hoodies-c-181-page-1.html",
    ]

    rules: Tuple[Rule, ...] = (
        # Rule(LinkExtractor(allow=r"page-[0-9]+")),
        Rule(
            LinkExtractor(allow=r"product[0-9]+"),
            callback="parse_item",
        ),
    )

    driver: Optional[WebDriver] = None

    splash_args: Dict[str, Any] = {
        "wait": 3.0,
        "timeout": 90,
        "resource_timeout": 20,
        "images": 0,
        "endpoint": "execute",
        "lua_source": PAGE_LOADING_WAIT_SCRIPT,
    }

    # Hoodie selectors
    NAME_XPATH: str = "/html/body/div[1]/div[5]/div[3]/h1/span[2]/text()"
    DISCOUNT_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[3]/div[1]/div[1]/span[3]/span/text()"
    INFO_KEYS_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[12]/div[2]/div[5]/div[1]/div//strong/text()"
    INFO_VALUES_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[12]/div[2]/div[5]/div[1]/div/div[2]/div/text()"
    TOTAL_REVIEWS_XPATH: str = "//*[@id='js_reviewCountText']/text()"
    ORIGINAL_PRICE_XPATH: str = "/html/body/div[1]/div[5]/div[3]/div[3]/div[1]/div[1]/span[3]/span/text()"

    # Hoodie reviews selectors
    REVIEWS_XPATH: str = "//div[@class='reviewinfo']"
    RATING_SELECTED_STARS_XPATH: str = (
        ".//p[@class='starscon_b dib']/i[@class='icon-star-black']"
    )
    TIMESTAMP_XPATH: str = ".//span[@class='reviewtime']/text()"
    TIMESTAMP_FORMAT: str = "%b,%d %Y %H:%M:%S"
    TEXT_XPATH: str = ".//p[@class='reviewcon']/text()"
    SIZE_XPATH: str = ".//p[@class='color-size']/span[1]/text()"
    COLOR_XPATH: str = ".//p[@class='color-size']/span[2]/text()"
    NEXT_REVIEWS_PAGE_XPATH: str = (
        '//*[@id="js_reviewPager"]/ul/li[{page_num}]/a'
    )

    product_id_counter: int = 0

    def parse_item(
        self, response: HtmlResponse
    ) -> Union[Iterable[Item], Iterable[SplashRequest]]:
        product_id: int = self.product_id_counter
        product_url: str = response.meta["splash"]["args"]["url"]
        name: str = response.xpath(self.NAME_XPATH).get("")

        original_price: float = float(
            response.xpath(self.ORIGINAL_PRICE_XPATH).get(0.0)
        )

        discount: int = int(response.xpath(self.DISCOUNT_XPATH).get(0))

        discounted_price: float = (
            original_price * discount / 100.0 if discount else 0.0
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

        response.meta["product_id"] = product_id
        response.meta["product_url"] = product_url

        if total_reviews > 0:
            yield from self.parse_item_reviews(response=response)

        self.product_id_counter = product_id + 1

    def parse_item_reviews(
        self,
        response: HtmlResponse,
    ) -> Union[Iterable[Item], Iterable[SplashRequest]]:
        product_id: int = response.meta["product_id"]
        product_url: str = response.meta["product_url"]
        page_num: int = 3

        try_next_page: bool = True

        while try_next_page:
            reviews: Optional[List[HtmlResponse]] = response.xpath(
                self.REVIEWS_XPATH
            )

            for review in reviews:
                rating: int = len(
                    review.xpath(self.RATING_SELECTED_STARS_XPATH).getall()
                )
                time: str = review.xpath(self.TIMESTAMP_XPATH).get("")
                timestamp: float = mktime(
                    datetime.strptime(time, self.TIMESTAMP_FORMAT).timetuple()
                )
                text: str = review.xpath(self.TEXT_XPATH).get("")
                size: str = (
                    review.xpath(self.SIZE_XPATH).get(": ").split(": ")[-1]
                )
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

            if not self.driver:
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                options.add_argument("--silent")
                options.add_argument("--log-level=3")

                self.driver = webdriver.Chrome(
                    executable_path=which("chromedriver"),
                    chrome_options=options,
                )

            self.driver.get(product_url)

            next_review_page_btn = self.driver.find_elements_by_xpath(
                self.NEXT_REVIEWS_PAGE_XPATH.format(page_num=page_num)
            )

            if next_review_page_btn and next_review_page_btn[0].text != ">":
                try:
                    next_review_page_btn[0].click()
                    self.driver.implicitly_wait(20)

                    selenium_response_text: str = self.driver.page_source
                    new_response: HtmlResponse = HtmlResponse(
                        url="", body=selenium_response_text, encoding="utf-8"
                    )
                    response = new_response
                    page_num += 1

                except Exception:
                    pass

            else:
                try_next_page = False

            self.driver.close()
            self.driver = None

    # Replace scrapy Request to splash Request
    # details: https://github.com/scrapy-plugins/scrapy-splash/issues/92
    def _build_request(self, rule_index, link):
        request: SplashRequest = SplashRequest(
            url=link.url,
            callback=self._callback,
            endpoint="execute",
            errback=self._errback,
            args=self.splash_args,
        )
        request.meta["rule"] = rule_index
        request.meta["link_text"] = link.text
        return request

    # Remove instance check for follow ups to work
    # details: https://github.com/scrapy-plugins/scrapy-splash/issues/92
    def _requests_to_follow(self, response):
        # if not isinstance(response, HtmlResponse):
        #     return
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
