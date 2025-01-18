# Funboost vs Scrapy

## 引言
在爬虫开发中，Scrapy是一种常用的框架。本文将通过一个爬虫示例对比Funboost和Scrapy这两者的优缺点。

## 示例代码
### Funboost 示例
以下是使用Funboost框架的爬虫代码示例，用于下载明星图片：

```python
from funboost import boost, BoosterParams
import requests
from parsel import Selector

@boost(BoosterParams(queue_name='xiaoxianrou_list_page', qps=0.2))
def crawl_list_page(page_index):
    """爬取列表页"""
    url = f'http://www.5442tu.com/mingxing/list_2_{page_index}.html'
    resp = requests.get(url)
    sel = Selector(resp.content.decode('gbk'))
    detail_sels = sel.xpath('//div[@class="imgList2"]/ul/li/a')
    for detail_sel in detail_sels:
        detail_url = detail_sel.xpath('./@href').extract_first()
        title = detail_sel.xpath('./@title').extract_first()
        crawl_detail_page.push(detail_url, title)

    # 翻页逻辑
    next_page = sel.xpath('//a[text()="下一页"]/@href').extract_first()
    if next_page:
        next_page_index = page_index + 1
        crawl_list_page.push(next_page_index)

@boost(BoosterParams(queue_name='xiaoxianrou_detail_page', qps=0.2))
def crawl_detail_page(detail_url, title):
    """爬取详情页"""
    resp = requests.get(detail_url)
    sel = Selector(resp.content.decode('gbk'))
    img_url = sel.xpath('//div[@class="imgContent"]//img/@src').extract_first()
    print(f'获取到图片: {title} - {img_url}')

if __name__ == '__main__':
    crawl_list_page.push(1)  # 从第1页开始爬取
    crawl_list_page.consume()
    crawl_detail_page.consume()
```

### Scrapy 示例
以下是使用Scrapy框架的爬虫代码示例：

```python
import scrapy
from scrapy_redis.spiders import RedisSpider

class XiaoxianrouSpider(RedisSpider):
    name = 'xiaoxianrou'
    allowed_domains = ['5442tu.com']
    start_urls = ["http://www.5442tu.com/mingxing/list_2_1.html"]

    def parse(self, response):
        """解析列表页"""
        detail_sels = response.xpath('//div[@class="imgList2"]/ul/li/a')
        for detail_sel in detail_sels:
            yield scrapy.Request(
                url=detail_sel.xpath('./@href').extract_first(),
                callback=self.parse_detail,
                meta={'title': detail_sel.xpath('./@title').extract_first()}
            )

        # 翻页逻辑
        next_page = response.xpath('//a[text()="下一页"]/@href').extract_first()
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse)

    def parse_detail(self, response):
        """解析详情页"""
        title = response.meta['title']
        img_url = response.xpath('//div[@class="imgContent"]//img/@src').extract_first()
        yield {
            'title': title,
            'img_url': img_url
        }
```

## 框架对比分析

### 1. 代码结构
- **Funboost**: 
  - 结构简单，灵活性高，用户可以自由编写请求逻辑，使用任何请求库。
  - 使用装饰器即可实现分布式功能，无需创建复杂的项目结构。

- **Scrapy**: 
  - 需要创建完整的项目结构，用户需要频繁在多个文件中来回切换写代码。
  - 必须遵循框架规范编写代码。
  - 文件较多，包括settings.py、items.py、pipelines.py等。

### 2. 学习成本
- **Funboost**:
  - 学习曲线平缓，用户只需掌握装饰器的使用，能够快速上手。

- **Scrapy**:
  - 学习曲线陡峭，需要理解框架的各个组件，增加了学习难度。

### 3. 功能特性
- **Funboost**:
  - 提供多种控制功能，支持高并发和灵活的任务调度，适合大规模爬虫项目。
  - 允许用户在函数中编写爬虫代码，支持多种消息队列。

- **Scrapy**:
  - 功能相对较弱，难以实现复杂的调度逻辑，扩展性较差。
  - 用户需要十分精通Scrapy框架本身，才能随心所欲地改造请求和实现独特的奇葩想法。

### 4. 代码迁移
- **Funboost**:
  - 对现有代码侵入性小
  - 只需添加装饰器即可
  - 保持原有代码逻辑不变

- **Scrapy**:
  - 在高并发场景下，Scrapy的性能表现不如Funboost。

## 结论
**Funboost在爬虫方面远远优于Scrapy，无论是灵活性、学习成本、功能特性还是性能，Funboost都能为开发者提供更好的体验。选择Funboost将使开发者能够更快速、高效地完成爬虫项目，真正实现爬虫的高效和便捷。**

此外，中国还有一大批仿Scrapy API用法的爬虫框架，例如Feapder，这些框架同样存在与Scrapy相似的问题，导致在使用难度和性能上远远落后于Funboost。
