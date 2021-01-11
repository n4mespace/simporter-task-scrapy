PAGE_LOADING_WAIT_SCRIPT: str = """
    function main(splash)
        splash:set_user_agent("Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36")
        splash.private_mode_enabled = false

        assert(splash:go(splash.args.url))
        assert(splash:wait(3))

        while not splash:select('span.curPrice.my-shop-price.js-dl-curPrice.shop-price-red > span') do
            assert(splash:wait(0.1))
        end

        return {
            html=splash:html()
        }
    end
"""
