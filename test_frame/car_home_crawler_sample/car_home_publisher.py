from test_frame.car_home_crawler_sample.car_home_consumer import crawl_list_page, crawl_detail_page

crawl_list_page.clear()   # 清空列表页
crawl_detail_page.clear()  # 清空详情页

# # 推送列表页首页
crawl_list_page.push('news', 1)  # 新闻
crawl_list_page.push('advice', page=1)  # 导购
crawl_list_page.push(news_type='drive', page=1)  # 驾驶评测
