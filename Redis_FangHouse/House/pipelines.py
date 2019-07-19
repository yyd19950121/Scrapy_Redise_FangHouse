# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exporters import JsonLinesItemExporter

class HousePipeline(object):
    def process_item(self, item, spider):
        return item

class HouseRedisPipeline(object):
    def __init__(self):
        
        self.newhouse_fp = open('new_house.json','wb')
        self.erhouse_fp = open('er_house.json','wb')

        self.newhouse_exporter = JsonLinesItemExporter(self.newhouse_fp,ensure_ascii = False)
        self.erhouse_exporter = JsonLinesItemExporter(self.erhouse_fp,ensure_ascii = False)


    
    # 保存json格式
    def process_item(self, item, spider):
        
        self.newhouse_exporter.export_item(item)
        self.erhouse_exporter.export_item(item)
        return item

    def close_spider(self,spider):
        self.newhouse_fp.close()
        self.erhouse_fp.close()