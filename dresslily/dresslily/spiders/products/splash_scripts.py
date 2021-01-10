NEXT_REVIEWS_PAGE: str = """
    function main(splash, args)
        assert(splash:go(args.url))
        assert(splash:wait(1))

        btn = splash:select('#js_reviewPager > ul > li:nth-child(3) > a')
        btn:mouse_click()

        assert(splash:wait(5))

        return {
            html = splash:html()
        }
    end
"""

PAGE_LOADING_WAIT: str = """
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
