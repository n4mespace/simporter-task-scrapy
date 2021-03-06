from abc import ABC, abstractmethod

from scrapy.exporters import CsvItemExporter
from scrapy import signals
from scrapy.item import ItemMeta

from .items import MenHoodieItem, ReviewItem


class SaveItemToCsvAbstractPipeline(ABC):
    SAVE_FOLDER: str = "scraped_data"

    @property
    @abstractmethod
    def item_name(self) -> str:
        ...

    @property
    @abstractmethod
    def item_class(self) -> ItemMeta:
        ...

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.file = open(f"{self.SAVE_FOLDER}/{self.item_name}.csv", "ab")
        self.exporter = CsvItemExporter(self.file)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        if isinstance(item, self.item_class):
            self.exporter.export_item(item)
        return item


class SaveMenHoodiesPipeline(SaveItemToCsvAbstractPipeline):
    item_name: str = "hoodies"
    item_class: ItemMeta = MenHoodieItem


class SaveReviewsPipeline(SaveItemToCsvAbstractPipeline):
    item_name: str = "reviews"
    item_class: ItemMeta = ReviewItem
