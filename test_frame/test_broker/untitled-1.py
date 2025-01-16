# coding=utf-8
import requests
from bs4 import BeautifulSoup
from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams

# 定义爬虫任务函数
@boost(BoosterParams(queue_name='test_queue70ac', do_task_filtering=True, qps=5, log_level=10, broker_exclusive_config={'a': 1}))
def crawl(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 解析数据，这里只是一个示例，你可以根据实际需求进行修改
    title = soup.title.string
    return title

# 运行爬虫
if __name__ == '__main__':
    # 假设你有一个 URL 列表
    urls = ['https://www.example.com', 'https://www.example.org', 'https://www.example.net']
    for url in urls:
        crawl.push(url)  # 将任务添加到队列中
    crawl.consume()  # 启动爬虫任务
