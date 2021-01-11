PAGE_LOADING_WAIT_SCRIPT: str = """
    function main(splash)
        assert(splash:go(splash.args.url))
        assert(splash:wait(5))

        while not splash:select('body > div.dl-page > div.good-main > div.good-hgap.good-basic-info > div.goodprice > div.goodprice-line > div.goodprice-line-start > span.curPrice.my-shop-price.js-dl-curPrice.shop-price-red > span') do
            assert(splash:wait(0.1))
        end

        return {
            html=splash:html()
        }
    end
"""
