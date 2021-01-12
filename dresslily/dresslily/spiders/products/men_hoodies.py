from scrapy import Item
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from scrapy.spiders import Rule

from shutil import which

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options

from time import mktime
from datetime import datetime

from typing import List, Tuple, Iterable, Optional, Dict, Any

from ...items import MenHoodieItem, ReviewItem
from ..splash_spider import SplashCrawlSpider

from ..splash_scripts import PAGE_LOADING_WAIT_SCRIPT


class MenHoodiesSpider(SplashCrawlSpider):
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

    splash_endpoint: str = "execute"
    splash_args: Dict[str, Any] = {
        "wait": 3.0,
        "timeout": 90,
        "resource_timeout": 20,
        "images": 0,
        "endpoint": splash_endpoint,
        "lua_source": PAGE_LOADING_WAIT_SCRIPT,
    }

    product_id_counter: int = 0

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

    REVIEWS_BY_PAGE_COUNT: int = 4

    def parse_item(self, response: HtmlResponse) -> Iterable[Item]:
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

        if total_reviews > 0:
            response.meta["product_id"] = product_id
            response.meta["product_url"] = product_url
            response.meta["total_reviews"] = total_reviews

            yield from self.parse_item_reviews(response=response)

        self.product_id_counter = product_id + 1

    def parse_item_reviews(self, response: HtmlResponse) -> Iterable[Item]:
        product_id: int = response.meta["product_id"]
        product_url: str = response.meta["product_url"]
        total_reviews: int = response.meta["total_reviews"]
        page_num: int = 2  # Starting with next page

        try_next_page: bool = True

        while try_next_page:
            reviews: List[HtmlResponse] = response.xpath(self.REVIEWS_XPATH)

            for review in reviews:
                rating: int = len(
                    review.xpath(self.RATING_SELECTED_STARS_XPATH).getall()
                )
                time: str = review.xpath(self.TIMESTAMP_XPATH).get("")
                timestamp: float = (
                    mktime(
                        datetime.strptime(
                            time, self.TIMESTAMP_FORMAT
                        ).timetuple()
                    )
                    if time
                    else 0.0
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

            try_next_page = False

            if total_reviews >= self.REVIEWS_BY_PAGE_COUNT * page_num:
                next_page_response: Optional[
                    HtmlResponse
                ] = self._try_get_next_reviews(page_num, product_url)
                if next_page_response:
                    response = next_page_response
                    try_next_page = True
                    page_num += 1

    def _try_get_next_reviews(
        self, page_num: int, product_url: str, retry_times: int = 4
    ) -> Optional[HtmlResponse]:
        new_response: Optional[HtmlResponse] = None

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--silent")
        options.add_argument("--log-level=3")

        driver: WebDriver = webdriver.Chrome(
            executable_path=which("chromedriver"), options=options
        )
        driver.get(product_url)
        driver.execute_script("document.body.style.zoom='zoom 1'")

        for _ in range(retry_times):
            new_response = self._get_next_reviews_with_driver(page_num, driver)

            if new_response:
                break

        driver.close()
        return new_response

    def _get_next_reviews_with_driver(
        self, page_num: int, driver: WebDriver
    ) -> Optional[HtmlResponse]:
        new_response: Optional[HtmlResponse] = None
        driver.refresh()

        try:
            next_page_xpath: str = self.NEXT_REVIEWS_PAGE_XPATH.format(
                page_num=page_num + 1
            )
            next_review_page_btn = driver.find_element_by_xpath(
                next_page_xpath
            )
            next_review_page_btn.click()

            driver.implicitly_wait(10)

            selenium_response_text: str = driver.page_source
            new_response = HtmlResponse(
                url="", body=selenium_response_text, encoding="utf-8"
            )

        except Exception as e:
            self.logger.warning(f"Can't parse reviews page: {page_num}")
            self.logger.error(e)

        finally:
            return new_response
