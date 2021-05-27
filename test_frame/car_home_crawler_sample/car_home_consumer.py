import requests
from parsel import Selector
from function_scheduling_distributed_framework import task_deco, BrokerEnum, run_consumer_with_multi_process

"""
演示分布式函数调度框架来驱动爬虫函数，使用此框架可以达使爬虫任务 自动调度、 分布式运行、确认消费万无一失、超高速自动并发、精确控频、
种子过滤(函数入参过滤实现的)、自动重试、定时爬取。可谓实现了一个爬虫框架应有的所有功能。

对于仿scrapy api写法框架的定义：
国内一众仿scrapy写法api的继承BaseSpider 重写 parse方法 里面yield Request(url,callback=annother_parse(另一个解析函数钩子))
举个请求百度的例子：
这只是文件之一只是请求百度而已就已经很多代码了，还没开始涉及多层级页面调度就已经，还有另外的配置文件规定中间件和并发控制。
xxframe

class FirstSpider(xxframe.xxSpider):
    def start_requests(self):
        yield xxframe.Request("https://www.baidu.com")

    def parse(self,  response):
        print(response)


此框架用于爬虫与仿scrapy的那种框架比，
有天壤之别，不仅是写法上简化10倍，在思想上前所未有的放荡不羁突破，可以实现任何想法，例如登录 selenium非常自然轻松的用于爬虫。
因为这与仿scrapy api框架对比，那就是极端自由的分布式函数调度框架 vs 被 scrapy框架内置Request对象限制的死死的url调度框架，
思维不是一个层次，国内作者的在github 爬虫框架，10有八九是仿scrapy写法框架，只是他的源码比scrapy少了，但是对于用户写法和扩展性仍然和scrapy一样烦躁死板。
函数调度框架 vs 仿scrapy框架，就是极端自由简单框架 pk 极度死板复杂框架。


此框架是自动调度一个函数，而不是自动调度一个url请求，一般框架是yield Requet(),所以不兼容用户自己手写requests urllib的请求，
如果用户对请求有特殊的定制，要么就需要手写中间件添加到框架的钩子，复杂的需要高度自定义的特殊请求在这些框架中甚至无法实现，极端不自由。

此框架由于是调度一个函数，在函数里面写 请求 解析 入库，用户想怎么写就怎么写，极端自由，使用户编码思想放荡不羁但整体上有统一的调度。
还能直接复用用户的老函数，例如之前是裸写requests爬虫，没有规划成使用框架爬虫，那么只要在函数上面加一个@task_deco的装饰器就可以自动调度了。

而90%一般爬虫框架与用户单线程手写测试 requests 请求解析存储，在流程逻辑和代码写法上是严重互斥的，要改造成使用这种框架改造会很大。
此框架如果用于爬虫和国内那些90%仿scrapy api的爬虫框架，在思想上完全不同，会使人眼界大开，思想之奔放与被scrapy api束缚死死的那种框架比起来有云泥之别。
因为国内的框架都是仿scrapy api，必须要继承框架的Spider基类，然后重写 def parse，然后在parse里面yield Request(url,callback=annother_parse)，
请求逻辑实现被 Request 类束缚得死死的，没有方便自定义的空间，一般都是要写middware拦截http请求的各个流程，写一些逻辑，那种代码极端不自由，而且怎么写middware，
也是被框架束缚的死死的，很难学,举个例子有人问scrapy  【process_response方法里面遇到503的时候怎么切换代理啊？】 ，
类似处理这些乱七八糟的想法如果是在正常的无scrapy框架的requests函数里面爬虫对99%python人员那就不是个事，if else轻松搞定。
分布式函数调度框架由于是自动调度函数而不是自动调度url发请求不需要按框架规矩设置各种中间件钩子，所以天生不存在这些问题。

用其他爬虫框架需要继承BaseSpider类，重写一大堆方法写一大堆中间件方法和配置文件，在很多个文件夹中来回切换写代码。
而用这个爬虫，只需要学习 @task_deco 一个装饰器就行，代码行数大幅度减少，随意重启代码任务万无一失，大幅度减少操心。

这个爬虫例子具有代表性，因为实现了演示从列表页到详情页的分布式自动调度。
如果使用仿scrapy api的框架来实现下面这个逻辑，那么代码文件数量，代码行数，自由度，尤其是执行速度会被全面暴击。
不是这个框架厉害，是由于一般爬虫框架作者思维被scrapy api束缚了，只能搞url调度框架，就没法和函数调度框架比了，
函数能实现一切用户想在函数里面写什么就写什么想实现什么就实现什么；
而url调度框架怎么请求url怎么扩展都是被框架束缚得死死的，用户没有高度自定义的余地(其实是有的，但需要非常之精通scrapy,99%的博客和教程不会涉及到这些偏门小众的想法)。
"""


@task_deco('car_home_list', broker_kind=BrokerEnum.REDIS_ACK_ABLE, max_retry_times=5, qps=6)
def crawl_list_page(news_type, page, do_page_turning=False):
    url = f'https://www.autohome.com.cn/{news_type}/{page}/#liststart'
    resp_text = requests.get(url).text
    sel = Selector(resp_text)
    for li in sel.css('ul.article > li'):
        if len(li.extract()) > 100:  # 有的是这样的去掉。 <li id="ad_tw_04" style="display: none;">
            url_detail = 'https:' + li.xpath('./a/@href').extract_first()
            title = li.xpath('./a/h3/text()').extract_first()
            crawl_detail_page.push(url_detail, title=title, news_type=news_type)  # 发布详情页任务
    if do_page_turning:
        last_page = int(sel.css('#channelPage > a:nth-child(12)::text').extract_first())
        for p in range(2, last_page + 1):
            crawl_list_page.push(news_type, p)  # 列表页翻页。


@task_deco('car_home_detail', broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=20,
           do_task_filtering=True, is_using_distributed_frequency_control=True)
def crawl_detail_page(url, title, news_type):
    resp_text = requests.get(url).text
    sel = Selector(resp_text)
    author = sel.css('#articlewrap > div.article-info > div > a::text').extract_first() or \
             sel.css('#articlewrap > div.article-info > div::text').extract_first() or ''
    author = author.replace("\n", "").strip()
    print(f'保存数据  {news_type}   {title} {author} {url} 到 数据库')  # 用户自由发挥保存。


if __name__ == '__main__':
    # crawl_list_page('news',1)
    crawl_list_page.consume()  # 启动列表页消费
    crawl_detail_page.consume()
    # 这样速度更猛，叠加多进程
    crawl_detail_page.multi_process_consume(2)

