from scrapy.spiders import CrawlSpider
from scrapy_splash import SplashRequest

from typing import Dict, Any


class SplashCrawlSpider(CrawlSpider):
    """
    Crawl pages due to specified rules via Splash

    details: https://github.com/scrapy-plugins/scrapy-splash/issues/92
    """

    # Define additional setting for SplashRequest
    splash_args: Dict[str, Any] = {}
    splash_endpoint: str = "render.html"

    def _build_request(self, rule_index, link):
        """
        Change scrapy.Request to scrapy_scpash.SplashRequest
        """
        request = SplashRequest(
            url=link.url,
            callback=self._callback,
            errback=self._errback,
            endpoint=self.splash_endpoint,
            args=self.splash_args,
        )
        request.meta["rule"] = rule_index
        request.meta["link_text"] = link.text
        request.meta["real_url"] = link.url
        return request

    def _requests_to_follow(self, response):
        """
        Remove instance check for follow ups to work
        """
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
