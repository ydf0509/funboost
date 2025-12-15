"""
可以单独部署启动消费，用户可以让booster随着fastapi一起启动，也可以单独启动消费。

因为 funboost.faas 是基于funboost注册到redis中的元数据，所以可以动态发现booster，
所以只要消费函数部署上线了，web服务完全无需重启，从http接口马上就能调用了，
相比传统web开发，加一个功能就要加一个接口，然后重启web，funboost faas爽的一逼。
"""

from funboost import BoosterDiscovery,BoostersManager

if __name__ == '__main__':
    # 演示 BoosterDiscovery ，自动扫描注册 @boost，
    # 效果等同于 直接 import task_funs_dir 下的add和sub模块。
    BoosterDiscovery(
        project_root_path=r'D:\codes\funboost',
        booster_dirs=['examples/example_faas/task_funs_dir'],
         ).auto_discovery()

    print(BoostersManager.get_all_queues())

    BoostersManager.consume_group('test_group1')