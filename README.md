# Simporter task (scraping)

### Project Description

Use Scrapy framework to parse data about men hoodies with reviews.

Website: https://www.dresslily.com/hoodies-c-181-page-1.html

Items to parse:

1. Men Hoodies
    ● product_id
    ● product_url
    ● name
    ● discount (%)
    ● discounted_price (0 if no sale)
    ● original_price
    ● total_reviews
    ● product_info (formatted string, e.g. “Occasion:Daily;Style:Fashion” )

2. Reviews
    ● product_id
    ● rating
    ● timestamp (convert review date to Unix timestamp)
    ● text
    ● size
    ● color

### Used tools
- Scrapy framework
- Splash

### Run crawler
1. Clone this repo and install dependencies (poetry recommended)
2. Run Splash
```sh
docker run -it -p 8050:8050 scrapinghub/splash --max-timeout 3600
```
3. Start crawler
```sh
cd dresslily
scrapy crawl men_hoodies
```
or
```sh
chmod +x ./start_crawler.sh
./start_crawler.sh
```

### Get data

After scraping finishes you can grab data in csv ([sample data](dresslily/scraped_data/))
- simporter-task-scrapy/dresslily/scraped_data/hoodies.csv
- simporter-task-scrapy/dresslily/scraped_data/reviews.csv
