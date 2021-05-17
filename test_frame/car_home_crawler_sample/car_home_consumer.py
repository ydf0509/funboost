import requests
from parsel import Selector
from function_scheduling_distributed_framework import task_deco, BrokerEnum, run_consumer_with_multi_process


@task_deco('car_home_list', broker_kind=BrokerEnum.REDIS_ACK_ABLE, max_retry_times=5, qps=2)
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


@task_deco('car_home_detail', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=600, qps=5, do_task_filtering=True)
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
