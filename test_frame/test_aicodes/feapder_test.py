
# feapder 2层级爬虫demo

# 导入feapder框架中的相关模块
from feapder import Item, Spider, Request

# 定义一个数据模型类，继承自feapder的Item类
class MyItem(Item):
    # 定义数据字段
    title = "default"
    url = "default"

# 定义一个爬虫类，继承自feapder的Spider类
class MySpider(Spider):
    # 定义起始URL
    start_urls = ["https://www.example.com"]

    # 解析函数，用于处理列表页
    def parse(self, request, response):
        # 使用xpath解析获取所有文章链接
        links = response.xpath('//div[@class="post-title"]/a/@href').extract()

        # 遍历链接列表，构造Request对象并发送
        for link in links:
            yield Request(link, callback=self.parse_detail)

    # 解析函数，用于处理详情页
    def parse_detail(self, request, response):
        # 实例化MyItem类
        item = MyItem()

        # 提取标题和URL
        item.title = response.xpath('//h1[@class="post-title"]/text()').extract_first()
        item.url = request.url

        # 返回数据
        yield item

# 运行爬虫
if __name__ == "__main__":
    MySpider().start()
