BOT_NAME = "dresslily"

SPIDER_MODULES = ["dresslily.spiders", "dresslily.spiders.products"]
NEWSPIDER_MODULE = "dresslily.spiders.products"
CONCURRENT_REQUESTS = 16

SPIDER_MIDDLEWARES = {
    # Splash setup
    "scrapy_splash.SplashDeduplicateArgsMiddleware": 100,
}

DOWNLOADER_MIDDLEWARES = {
    # Splash setup
    "scrapy_splash.SplashCookiesMiddleware": 723,
    "scrapy_splash.SplashMiddleware": 725,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

ITEM_PIPELINES = {
    # Save items to .csv
    "dresslily.pipelines.MenHoodiePipeline": 300,
    "dresslily.pipelines.ReviewPipeline": 301,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 30

# Splash setup
SPLASH_URL = "http://localhost:8050"
DUPEFILTER_CLASS = "scrapy_splash.SplashAwareDupeFilter"
HTTPCACHE_STORAGE = "scrapy_splash.SplashAwareFSCacheStorage"
