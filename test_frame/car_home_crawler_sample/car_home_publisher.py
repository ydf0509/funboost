from function_scheduling_distributed_framework import fsdf_background_scheduler
from test_frame.car_home_crawler_sample.car_home_consumer import crawl_list_page, crawl_detail_page

crawl_list_page.clear()  # 清空列表页
crawl_detail_page.clear()  # 清空详情页

# # 推送列表页首页，同时设置翻页为True
crawl_list_page.push('news', 1, do_page_turning=True)  # 新闻
crawl_list_page.push('advice', page=1, do_page_turning=True)  # 导购
crawl_list_page.push(news_type='drive', page=1, do_page_turning=True)  # 驾驶评测


for news_typex in ['news', 'advice', 'drive']:  # 定时任务，语法入参是apscheduler包相同。每隔120秒查询一次首页更新,这个可以不要。
    fsdf_background_scheduler.add_timing_publish_job(crawl_list_page, 'interval', seconds=120, kwargs={"news_type": news_typex, "page": 1, "do_page_turning": False})
fsdf_background_scheduler.start()  # 启动首页查询有没有新的新闻的定时发布任务
