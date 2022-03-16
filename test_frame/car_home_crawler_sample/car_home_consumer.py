import requests
from parsel import Selector
from funboost import boost, BrokerEnum, IdeAutoCompleteHelper

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

用其他爬虫框架需要继承BaseSpider类，重写一大堆方法写一大堆中间件方法和配置文件，在很多个文件夹中来回切换写代码。
而用这个爬虫，只需要学习 @boost 一个装饰器就行，代码行数大幅度减少，随意重启代码任务万无一失，大幅度减少操心。

这个爬虫例子具有代表性，因为实现了演示从列表页到详情页的分布式自动调度。

"""

"""
除了以上解释的最重要的极端自由的自定义请求解析存储，比普通爬虫框架更强的方面还有：
2、此爬虫框架支持 redis_ack_able rabbitmq模式，在爬虫大规模并发请求中状态时候，能够支持随意重启代码，种子任务万无一失，
   普通人做的reids.blpop，任务取出来正在消费，但是突然关闭代码再启动，瞬间丢失大量任务，这种框架那就是个伪断点接续。
3、此框架不仅能够支持恒定并发数量爬虫，也能支持恒定qps爬虫。例如规定1秒钟爬7个页面，一般人以为是开7个线程并发，这是大错特错，
  服务端响应时间没说是永远都刚好精确1秒，只有能恒定qps运行的框架，才能保证每秒爬7个页面，恒定并发数量的框架差远了。
4、能支持 任务过滤有效期缓存，普通爬虫框架全部都只能支持永久过滤，例如一个页面可能每周都更新，那不能搞成永久都过滤任务。
因为此框架带有20多种控制功能，所以普通爬虫框架能实现的控制，这个全部都自带了。
"""


@boost('car_home_list', broker_kind=BrokerEnum.RedisBrpopLpush, max_retry_times=5, qps=2)
def crawl_list_page(news_type, page, do_page_turning=False):
    url = f'https://www.autohome.com.cn/{news_type}/{page}/#liststart'
    resp_text = requests.get(url).text  # 如果要换ip 换请求头，自己写一个自动换ip和请求头的请求函数就行了太简单了，不需要按照某些框架写啥请求中间件类来改变请求行为。
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


@boost('car_home_detail', broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=3,
       do_task_filtering=True, is_using_distributed_frequency_control=True)
def crawl_detail_page(url, title, news_type):
    resp_text = requests.get(url).text # # 如果要换ip 换请求头，自己写一个自动换ip和请求头的请求函数就行了太简单了，不需要按照某些框架写啥请求中间件类来改变请求行为。
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
    # crawl_detail_page.multi_process_consume(4)



