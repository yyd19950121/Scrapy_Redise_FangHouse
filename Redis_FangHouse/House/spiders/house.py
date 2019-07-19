# -*- coding: utf-8 -*-
import scrapy
import re
from House.items import HouseItem,OldHouseItem



class HouseSpider(scrapy.Spider):
    name = 'house'

    start_urls = ['https://www.fang.com/SoufunFamily.htm']

    # 从redis哪读取url
    # redis_key = 'fang:start_urls' # 从这里去读取url(加冒号是加以区分)

    def parse(self, response):
        #获取每行
        trs = response.xpath('//div[@class="outCont"]//tr')
        province = None

        for tr in trs:
            #将第一个td标签过滤掉
            tds = tr.xpath('.//td[not(@class)]')
            #获取省份
            province_text = tds[0].xpath('.//text()').get()
            # 第二行前面没有省份的,将其替换掉第一行获取到的省份
            province_text = re.sub(r"\s","",province_text)

            if province_text:
                province = province_text

            # 不爬取 海外的
            if province =='其它':
                continue

            # 获取城市的td
            city_tds = tds[1]
            city_links = city_tds.xpath('.//a') #每个城市的url

            # 遍历每个城市的 a 标签
            for city in city_links:
                # 城市的名字
                city_name = city.xpath('.//text()').get()
                # 城市的链接
                city_link = city.xpath('.//@href').get()

                # 检测一下
                # print("省份:",province)
                # print("城市:",city_name)
                # print("城市链接:",city_link)

                # 获取每个 每个城市的 缩写字母
                city_word= city_link.split('//')[1].split('.')[0]
                if 'bj' in city_word:
                    new_house_url = 'https://newhouse.fang.com/house/s/'
                    er_house_url = 'https://esf1.fang.com/'

                else:
                    # 每个城市的新房链接
                    new_house_url = 'https://'+ str(city_word)+'.newhouse.fang.com/house/s/'
                    # 每个城市的二手房链接
                    er_house_url = 'https://'+ str(city_word)+'.esf.fang.com/'

                #检测一下
                # print("城市:",province,city_name)
                # print("新手房链接:",new_house_url)
                # print("二手房链接:",er_house_url)

                # 解析 新房页面
                print("!!",new_house_url)
                yield scrapy.Request(
                    url=new_house_url,
                    callback=self.parse_new_house,
                    meta={'info':(province,city_name)}
                )

                # 解析二手房页面
                print("**",er_house_url)
                yield scrapy.Request(
                    url=er_house_url,
                    callback=self.er_house,
                    meta={'info':(province,city_name)}
                )




    # 解析新手房信息(需要先和获取每页的url,再对每页进行解析提取信息)
    def parse_new_house(self,response):
        province,city = response.meta.get('info')


        # 获取所有LI
        lis = response.xpath('//div[contains(@class,"nl_con clearfix")]/ul/li//div[@class="nlc_details"]')
        for li in lis:

            #小区名
            name = li.xpath('.//div[@class="nlcd_name"]/a/text()').get().strip()


            # 格局 ['2居', '3居']
            rooms_type_list = li.xpath('.//div[@class="house_type clearfix"]/a/text()').getall()
            # rooms_type_list = list(map(lambda x:re.sub(r"\s",'',x),rooms_type_list)) # 可以不进行这一步
            # 进行过滤,只保留(什么居)的数据 例如: ['2居', '3居']
            rooms = list(filter(lambda x:x.endswith('居'),rooms_type_list)) #不符合条件的为[] 空列表

            # 面积
            area = li.xpath('.//div[@class="house_type clearfix"]/text()').getall() #得到列表
            area = ''.join(area)
            area = re.sub(r'\s|－|/','',area)



            # 地址
            address = li.xpath('..//div[@class="address"]/a/@title').get()

            # 销售状态
            sale = li.xpath('.//div[@class="fangyuan"]/span/text()').get()


            # 价格
            price = li.xpath('.//div[contains(@class,"nhouse_price")or contains(@class,"kanesf")]//text()').getall()
            price = ''.join(price).strip()
            price = re.sub(r'\s|广告','',price)
            # print(price)

            # 详情url
            urigin_url = li.xpath('.//div[@class="nlcd_name"]/a/@href').get()
            urigin_url = 'http:'+urigin_url



            item = HouseItem()
            item['province'] = province
            item['city'] = city
            item['name'] = name
            item['price'] = price
            item['rooms'] = rooms
            item['area'] = area
            item['address'] = address

            item['sale'] = sale
            item['urigin_url'] = urigin_url

            yield item
            print(item)

        #获取下一页的url
        next_url = response.xpath('//div[@class="page"]//a[@class="next"]/@href').get()
        if next_url:
            next_url = 'https://newhouse.fang.com'+next_url
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_new_house,
                meta={'info':(province,city)}
            )


    # 解析二手房信息
    def er_house(self,response):
        province, city = response.meta.get('info')

        # #获取所有的dl
        dl_list = response.xpath('//div[@class="shop_list shop_list_4"]/dl[contains(@class,"clearfix") and contains(@id,"kesfqbfylb")]')
        for dl in dl_list:
            item = OldHouseItem(province=province,city=city)
            # 名字
            name = dl.xpath('.//dd/p[@class="add_shop"]/a/@title').get()


            # 房子信息
            infos = dl.xpath('.//dd/p[@class="tel_shop"]//text()').getall()
            infos = list(map(lambda x:re.sub(r'\s|\|','',x),infos))
            infos = filter(None,infos)


            for info in infos:

                if '厅' in info:
                    item['rooms'] = info
                elif '层' in info:
                    item['floor'] =  info
                elif '向' in info:
                    item['toward'] = info
                elif '建' in info:
                    item['year'] = info
                elif '㎡' in info:
                    item['arra'] = info


            # 地址
            address = dl.xpath('.//dd/p[@class="add_shop"]/span/text()').get()



            # # 总价
            price = dl.xpath('.//dd[@class="price_right"]/span[@class="red"]//text()').getall()
            price = ''.join(price).strip()
            # 单价
            unit = dl.xpath('.//dd[@class="price_right"]/span[2]/text()').get()
            # 原始的url
            origin_url = dl.xpath('.//dd/h4[@class="clearfix"]/a/@href').get()
            origin_url = 'https://hf.esf.fang.com'+''.join(origin_url)


            item['name'] = name
            item['address'] = address
            item['price'] = price
            item['unit'] = unit
            item['origin_url'] = origin_url

            yield item

        # 下一页的url
        next_url = response.xpath('//div[@class="page_al"]//p[1]/a/@href').get()
        next_url = response.urljoin(next_url)
        yield scrapy.Request(
            url=next_url,
            callback=self.er_house,
            meta={'info':(province,city)}
        )







            







