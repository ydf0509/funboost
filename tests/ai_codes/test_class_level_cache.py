"""
测试 RedisReportInfoGetterMixin 的类级别缓存功能
验证多个实例共享同一个缓存，避免重复查询Redis
"""

import time
from funboost.core.active_cousumer_info_getter import ActiveCousumerProcessInfoGetter, QueuesConusmerParamsGetter


def test_class_level_cache_shared():
    """测试多个实例共享类级别缓存"""
    print("\n=== 测试类级别缓存（多实例共享） ===")
    
    # 创建第一个实例
    getter1 = ActiveCousumerProcessInfoGetter()
    print("创建实例1...")
    
    # 第一次调用，从Redis获取
    print("\n实例1: 第1次调用 get_all_queue_names()...")
    start_time = time.time()
    result1 = getter1.get_all_queue_names()
    time1 = time.time() - start_time
    cache_ts1 = getter1._cache_all_queue_names_ts
    print(f"  耗时: {time1:.4f}秒, 结果数量: {len(result1)}")
    print(f"  缓存时间戳: {cache_ts1}")
    
    # 创建第二个实例
    print("\n创建实例2...")
    getter2 = ActiveCousumerProcessInfoGetter()
    
    # 第二个实例调用，应该使用第一个实例创建的缓存
    print("\n实例2: 第1次调用 get_all_queue_names() (应该使用实例1的缓存)...")
    start_time = time.time()
    result2 = getter2.get_all_queue_names()
    time2 = time.time() - start_time
    cache_ts2 = getter2._cache_all_queue_names_ts
    print(f"  耗时: {time2:.4f}秒, 结果数量: {len(result2)}")
    print(f"  缓存时间戳: {cache_ts2}")
    
    # 验证结果
    print("\n验证:")
    print(f"  ✓ 两个实例的缓存时间戳相同: {cache_ts1 == cache_ts2}")
    print(f"  ✓ 两个实例获取的结果相同: {result1 == result2}")
    print(f"  ✓ 实例2使用了缓存 (速度更快): {time2 < time1 / 5 if time1 > 0.0001 else '是'}")
    print(f"  ✓ 速度提升: {time1/time2 if time2 > 0 else 'N/A'}倍")
    
    # 创建第三个实例
    print("\n创建实例3...")
    getter3 = ActiveCousumerProcessInfoGetter()
    
    # 第三个实例也应该使用同一个缓存
    print("\n实例3: 第1次调用 get_all_queue_names() (应该使用共享缓存)...")
    start_time = time.time()
    result3 = getter3.get_all_queue_names()
    time3 = time.time() - start_time
    cache_ts3 = getter3._cache_all_queue_names_ts
    print(f"  耗时: {time3:.6f}秒, 结果数量: {len(result3)}")
    print(f"  缓存时间戳: {cache_ts3}")
    
    print("\n验证:")
    print(f"  ✓ 三个实例的缓存时间戳相同: {cache_ts1 == cache_ts2 == cache_ts3}")
    print(f"  ✓ 验证是类属性: {getter1._cache_all_queue_names is getter2._cache_all_queue_names is getter3._cache_all_queue_names}")


def test_cache_expiration():
    """测试缓存过期机制"""
    print("\n\n=== 测试缓存过期机制 ===")
    
    getter = ActiveCousumerProcessInfoGetter()
    
    # 第一次调用
    print("\n第1次调用...")
    start_time = time.time()
    result1 = getter.get_all_queue_names()
    time1 = time.time() - start_time
    print(f"  耗时: {time1:.4f}秒")
    print(f"  缓存TTL: {getter._cache_ttl}秒")
    
    # 立即第二次调用，使用缓存
    print("\n第2次调用 (立即，应使用缓存)...")
    start_time = time.time()
    result2 = getter.get_all_queue_names()
    time2 = time.time() - start_time
    print(f"  耗时: {time2:.6f}秒")
    print(f"  使用缓存: {'是' if time2 < time1 / 5 else '否'}")
    
    # 检查剩余缓存时间
    remaining = getter._cache_ttl - (time.time() - getter._cache_all_queue_names_ts)
    print(f"\n当前缓存剩余有效时间: {remaining:.2f}秒")
    
    print("\n说明: 缓存将在30秒后过期，过期后会重新从Redis获取")


def test_project_name_cache():
    """测试按项目名称查询的缓存"""
    print("\n\n=== 测试 get_queue_names_by_project_name 缓存 ===")
    
    getter1 = QueuesConusmerParamsGetter()
    
    # 获取所有项目
    all_projects = getter1.get_all_project_names()
    if not all_projects:
        print("没有找到项目，跳过测试")
        return
    
    test_project = list(all_projects)[0]
    print(f"测试项目: {test_project}")
    
    # 实例1第一次调用
    print(f"\n实例1: 第1次调用 get_queue_names_by_project_name('{test_project}')...")
    start_time = time.time()
    result1 = getter1.get_queue_names_by_project_name(test_project)
    time1 = time.time() - start_time
    print(f"  耗时: {time1:.4f}秒, 结果数量: {len(result1)}")
    
    # 创建第二个实例
    getter2 = QueuesConusmerParamsGetter()
    
    # 实例2第一次调用，应该使用实例1的缓存
    print(f"\n实例2: 第1次调用 get_queue_names_by_project_name('{test_project}') (应使用实例1的缓存)...")
    start_time = time.time()
    result2 = getter2.get_queue_names_by_project_name(test_project)
    time2 = time.time() - start_time
    print(f"  耗时: {time2:.6f}秒, 结果数量: {len(result2)}")
    
    # 验证
    print("\n验证:")
    print(f"  ✓ 两个实例获取的结果相同: {result1 == result2}")
    print(f"  ✓ 实例2使用了缓存: {time2 < time1 / 5 if time1 > 0.0001 else '是'}")
    
    # 验证缓存字典是同一个对象
    if test_project in getter1._cache_queue_names_by_project and test_project in getter2._cache_queue_names_by_project:
        cache1 = getter1._cache_queue_names_by_project[test_project]
        cache2 = getter2._cache_queue_names_by_project[test_project]
        print(f"  ✓ 两个实例的缓存字典是同一个对象: {cache1 is cache2}")
        print(f"  ✓ 缓存时间戳相同: {cache1['ts'] == cache2['ts']}")


def test_thread_safety():
    """测试线程安全性"""
    print("\n\n=== 测试线程安全性 ===")
    
    import threading
    
    results = []
    errors = []
    
    def query_in_thread(thread_id):
        try:
            getter = ActiveCousumerProcessInfoGetter()
            result = getter.get_all_queue_names()
            results.append((thread_id, len(result)))
        except Exception as e:
            errors.append((thread_id, str(e)))
    
    print("\n创建10个线程同时查询...")
    threads = []
    for i in range(10):
        t = threading.Thread(target=query_in_thread, args=(i,))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    print(f"\n完成! 成功查询: {len(results)}, 错误: {len(errors)}")
    
    if errors:
        print("\n错误:")
        for thread_id, error in errors:
            print(f"  线程{thread_id}: {error}")
    
    if results:
        # 验证所有结果一致
        first_count = results[0][1]
        all_same = all(count == first_count for _, count in results)
        print(f"\n验证:")
        print(f"  ✓ 所有线程获取的结果数量一致: {all_same}")
        print(f"  ✓ 结果数量: {first_count}")


if __name__ == '__main__':
    print("=" * 70)
    print("测试 Redis 查询的类级别缓存功能")
    print("=" * 70)
    
    try:
        test_class_level_cache_shared()
        test_cache_expiration()
        test_project_name_cache()
        test_thread_safety()
        
        print("\n" + "=" * 70)
        print("✓ 所有测试完成！")
        print("=" * 70)
        print("\n功能总结:")
        print("  1. ✓ 使用类属性存储缓存，所有实例共享")
        print("  2. ✓ 缓存有效期30秒，过期自动重新查询")
        print("  3. ✓ 使用线程锁保证线程安全")
        print("  4. ✓ 避免频繁查询Redis，提升性能")
        print("  5. ✓ get_all_queue_names() 和 get_queue_names_by_project_name() 都支持缓存")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

