BOT_NAME = "dresslily"

SPIDER_MODULES = ["dresslily.spiders", "dresslily.spiders.products"]
NEWSPIDER_MODULE = "dresslily.spiders.products"
CONCURRENT_REQUESTS = 16

SPIDER_MIDDLEWARES = {
    # Splash setup
    "scrapy_splash.SplashDeduplicateArgsMiddleware": 100,
}

DOWNLOADER_MIDDLEWARES = {
    # Retraing
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 500,
    # Splash setup
    "scrapy_splash.SplashCookiesMiddleware": 723,
    "scrapy_splash.SplashMiddleware": 725,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408]

ITEM_PIPELINES = {
    # Save items to .csv
    # "dresslily.pipelines.MenHoodiePipeline": 300,
    # "dresslily.pipelines.ReviewPipeline": 301,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 10
AUTOTHROTTLE_MAX_DELAY = 120

# Splash setup
SPLASH_URL = "http://localhost:8050"
DUPEFILTER_CLASS = "scrapy_splash.SplashAwareDupeFilter"
HTTPCACHE_STORAGE = "scrapy_splash.SplashAwareFSCacheStorage"
