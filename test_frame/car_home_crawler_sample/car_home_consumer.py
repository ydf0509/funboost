import requests
from parsel import Selector
from function_scheduling_distributed_framework import task_deco, BrokerEnum, run_consumer_with_multi_process

"""
演示分布式函数调度框架来驱动爬虫函数，使用此框架可以达使爬虫任务 自动调度、 分布式运行、确认消费万无一失、超高速自动并发、精确控频、
种子过滤(函数入参过滤实现的)、自动重试、定时爬取。可谓实现了一个爬虫框架应有的所有功能。

此框架是自动调度一个函数，而不是自动调度一个url请求，一般框架是yield Requet(),所以不兼容用户自己手写requests urllib的请求，
如果用户对请求有特殊的定制，要么就需要手写中间件添加到框架的钩子，复杂的需要高度自定义的特殊请求在这些框架中甚至无法实现，极端不自由。

此框架由于是调度一个函数，在函数里面写 请求 解析 入库，用户想怎么写就怎么写，极端自由，使用户编码思想放荡不羁但整体上有统一的调度。
还能直接复用用户的老函数，例如之前是裸写requests爬虫，没有规划成使用框架爬虫，那么只要在函数上面加一个@task_deco的装饰器就可以自动调度了。

而90%一般普通爬虫框架与用户手写requests 请求解析存储，在流程逻辑上是严重互斥的，要改造成使用这种框架改造会很大。
此框架如果用于爬虫和国内那些90%仿scrapy api的爬虫框架，在思想上完全不同，会使人眼界大开，思想之奔放与被scrapy api束缚死死的那种框架比起来有云泥之别。
因为国内的框架都是仿scrapy api，必须要继承框架的Spider基类，然后重写 def parse，然后在parse里面yield Request(url,callback=annother_parse)，
请求逻辑实现被 Request 类束缚得死死的，没有方便自定义的空间，一般都是要写middware拦截http请求的各个流程，写一些逻辑，那种代码极端不自由，而且怎么写middware，
也是被框架束缚的死死的，很难学。分布式函数调度框架由于是自动调度函数而不是自动调度url请求，所以天生不存在这些问题。


这个爬虫例子具有代表性，因为实现了演示从列表页到详情页的分布式自动调度。

"""


@task_deco('car_home_list', broker_kind=BrokerEnum.REDIS_ACK_ABLE, max_retry_times=5, qps=0.1)
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


@task_deco('car_home_detail', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=600, qps=0.2,
           do_task_filtering=True,is_using_distributed_frequency_control=True)
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
    # 这样速度更猛，叠加多进程
    run_consumer_with_multi_process(crawl_detail_page, 2)

