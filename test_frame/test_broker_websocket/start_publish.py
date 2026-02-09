# -*- coding: utf-8 -*-
"""
发布 WebSocket 消息

直接运行此脚本即可发布测试消息
注意：需要先启动 WebSocket 服务器 (start_ws_server.py)
"""

from start_consume import process_message

if __name__ == '__main__':
    print("=" * 50)
    print("发布 WebSocket 消息")
    print("=" * 50)
    
    total_cnt = 20000
    
    for i in range(total_cnt):
        process_message.push(x=i, y=i * 10)
        if i%1000==0:
            print(f"已发布: {i}/{total_cnt}")
    
    print("=" * 50)
    print(f"发布完成！共 {total_cnt} 条消息")
    print("=" * 50)
