# test_api_client.py
import requests
import time
import json

# Web API 的基础 URL
BASE_URL = "http://127.0.0.1:5000"

def print_step(message):
    """格式化打印步骤标题"""
    print("\n" + "="*50)
    print(f"  {message}")
    print("="*50)

def add_task(task_id, interval, message):
    """调用 API 添加一个定时任务"""
    url = f"{BASE_URL}/add_task"
    payload = {
        "task_id": task_id,
        "interval_seconds": interval,
        "message": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 如果请求失败则抛出异常
        print(f"添加任务 '{task_id}' 成功: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"添加任务 '{task_id}' 失败: {e}")

def get_tasks():
    """调用 API 查看所有定时任务"""
    url = f"{BASE_URL}/get_tasks"
    try:
        response = requests.get(url)
        response.raise_for_status()
        tasks = response.json()
        print("当前已安排的任务:")
        if not tasks:
            print("  - (无)")
        else:
            for task in tasks:
                print(f"  - ID: {task['id']}, 下次运行时间: {task['next_run_time']}")
        return tasks
    except requests.exceptions.RequestException as e:
        print(f"获取任务列表失败: {e}")
        return []

def remove_task(task_id):
    """调用 API 删除一个定时任务"""
    url = f"{BASE_URL}/remove_task/{task_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        print(f"删除任务 '{task_id}' 成功: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"删除任务 '{task_id}' 失败: {e}")


if __name__ == "__main__":
    print_step("步骤 1: 添加两个定时任务")
    add_task("task_A", 5, "这是任务A，每5秒一次")
    add_task("task_B", 8, "这是任务B，每8秒一次")
    time.sleep(1)

    print_step("步骤 2: 查看当前的任务列表")
    get_tasks()

    wait_seconds = 20
    print_step(f"步骤 3: 等待 {wait_seconds} 秒，观察后台 Worker 的输出...")
    for i in range(wait_seconds, 0, -1):
        print(f"\r倒计时: {i} 秒...", end="")
        time.sleep(1)
    print("\n等待结束。")

    # print_step("步骤 4: 删除任务 'task_A'")
    # remove_task("task_A")
    # time.sleep(1)
    #
    # print_step("步骤 5: 再次查看当前的任务列表，确认 'task_A' 已被删除")
    # get_tasks()
    #
    # print("\n客户端测试执行完毕。")
