# coding=utf-8
import requests
from bs4 import BeautifulSoup
from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams

# 定义一级页面爬虫任务函数
@boost(BoosterParams(queue_name='level1_queue', do_task_filtering=True, qps=5, log_level=10, broker_exclusive_config={'a': 1}))
def crawl_level1(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 提取二级页面的链接
    level2_links = [a['href'] for a in soup.find_all('a', href=True)]
    return level2_links

# 定义二级页面爬虫任务函数
@boost(BoosterParams(queue_name='level2_queue', do_task_filtering=True, qps=5, log_level=10, broker_exclusive_config={'a': 1}))
def crawl_level2(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 解析数据，这里只是一个示例，你可以根据实际需求进行修改
    title = soup.title.string
    return title

# 运行爬虫
if __name__ == '__main__':
    # 假设你有一个一级页面的 URL
    level1_url = 'https://www.example.com'
    crawl_level1.push(level1_url)  # 将任务添加到队列中
    crawl_level1.consume()  # 启动一级页面爬虫任务
    # 处理一级页面返回的二级页面链接
    for level2_url in crawl_level1.get_result():
        crawl_level2.push(level2_url)  # 将任务添加到队列中
    crawl_level2.consume()  # 启动二级页面爬虫任务
