from function_scheduling_distributed_framework import task_deco, BrokerEnum
import requests
from parsel import Selector


@task_deco('car_home_list', broker_kind=BrokerEnum.REDIS_ACK_ABLE, max_retry_times=5, qps=3)
def crawl_list_page(news_type, page):
    url = f'https://www.autohome.com.cn/{news_type}/{page}/#liststart'
    resp_text = requests.get(url).text
    sel = Selector(resp_text)
    for li in sel.css('#Ul1 > li'):
        url_detail = 'https:' + li.xpath('./a/@href').extract_first()
        title = li.xpath('./a/h3/text()').extract_first()
        crawl_detail_page.push(url_detail, title=title, news_type=news_type)
    if page == 1:
        last_page = int(sel.css('#channelPage > a:nth-child(12)::text').extract_first())
        for p in range(2, last_page + 1):
            crawl_list_page.push(news_type, p)


@task_deco('car_home_detail', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=100, qps=8, do_task_filtering=True)
def crawl_detail_page(url, title, news_type):
    resp_text = requests.get(url).text
    sel = Selector(resp_text)
    author = sel.css('#articlewrap > div.article-info > div > a::text').extract_first() or \
             sel.css('#articlewrap > div.article-info > div::text').extract_first() or ''
    author = author.replace("\n", "").strip()
    print(f'使用print模拟保存到数据库  {news_type}   {title} {author} {url}')  # ，实际为调用数据库插入函数，压根不需要return item出来在另外文件的地方进行保存。


if __name__ == '__main__':
    crawl_list_page.consume()
    crawl_detail_page.consume()
