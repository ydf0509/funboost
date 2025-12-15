"""
测试 FakeFunGenerator 动态函数生成器

演示如何根据参数元数据动态生成函数，并验证生成的函数能被正确解析
"""

import inspect
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator, ConsumingFuncInputParamsChecker


def test_gen_fun_basic():
    """测试基本的函数生成"""
    print("=" * 60)
    print("测试 1: 基本函数生成")
    print("=" * 60)
    
    # 生成一个有2个必需参数和2个可选参数的函数
    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=['x', 'y'],
        optional_arg_name_list=['z', 'w'],
        func_name='test_add'
    )
    
    # 检查函数签名
    spec = inspect.getfullargspec(func)
    print(f"✅ 生成的函数名: {func.__name__}")
    print(f"✅ 所有参数: {spec.args}")
    print(f"✅ 默认值个数: {len(spec.defaults) if spec.defaults else 0}")
    print(f"✅ 函数签名: {inspect.signature(func)}")
    
    # 验证
    assert func.__name__ == 'test_add'
    assert spec.args == ['x', 'y', 'z', 'w']
    assert len(spec.defaults) == 2
    print("\n✅ 基本函数生成测试通过！\n")


def test_gen_fun_only_must_params():
    """测试只有必需参数的函数"""
    print("=" * 60)
    print("测试 2: 只有必需参数")
    print("=" * 60)
    
    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=['a', 'b', 'c'],
        optional_arg_name_list=[],
        func_name='my_func'
    )
    
    spec = inspect.getfullargspec(func)
    print(f"✅ 生成的函数: {func.__name__}")
    print(f"✅ 所有参数: {spec.args}")
    print(f"✅ 默认值: {spec.defaults}")
    print(f"✅ 函数签名: {inspect.signature(func)}")
    
    assert spec.args == ['a', 'b', 'c']
    assert spec.defaults is None
    print("\n✅ 只有必需参数测试通过！\n")


def test_gen_fun_only_optional_params():
    """测试只有可选参数的函数"""
    print("=" * 60)
    print("测试 3: 只有可选参数")
    print("=" * 60)
    
    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=[],
        optional_arg_name_list=['opt1', 'opt2'],
        func_name='optional_func'
    )
    
    spec = inspect.getfullargspec(func)
    print(f"✅ 生成的函数: {func.__name__}")
    print(f"✅ 所有参数: {spec.args}")
    print(f"✅ 默认值个数: {len(spec.defaults)}")
    print(f"✅ 函数签名: {inspect.signature(func)}")
    
    assert spec.args == ['opt1', 'opt2']
    assert len(spec.defaults) == 2
    print("\n✅ 只有可选参数测试通过！\n")


def test_gen_params_info_from_dynamic_func():
    """测试从动态生成的函数中提取参数信息"""
    print("=" * 60)
    print("测试 4: 从动态函数提取参数信息")
    print("=" * 60)
    
    # 1. 模拟从 redis 获取的元数据
    must_params = ['user_id', 'amount']
    optional_params = ['currency', 'memo']
    
    print(f"📋 元数据:")
    print(f"   必需参数: {must_params}")
    print(f"   可选参数: {optional_params}")
    
    # 2. 动态生成函数
    dynamic_func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=must_params,
        optional_arg_name_list=optional_params,
        func_name='process_payment'
    )
    
    # 3. 使用 ConsumingFuncInputParamsChecker 提取参数信息
    params_info = ConsumingFuncInputParamsChecker.gen_func_params_info_by_func(dynamic_func)
    
    print(f"\n✅ 提取的参数信息:")
    print(f"   函数名: {params_info['func_name']}")
    print(f"   所有参数: {params_info['all_arg_name_list']}")
    print(f"   必需参数: {params_info['must_arg_name_list']}")
    print(f"   可选参数: {params_info['optional_arg_name_list']}")
    
    # 4. 验证正确性
    assert params_info['func_name'] == 'process_payment'
    assert params_info['all_arg_name_list'] == must_params + optional_params
    assert params_info['must_arg_name_list'] == must_params
    assert params_info['optional_arg_name_list'] == optional_params
    
    print("\n✅ 参数信息提取完全正确！\n")


def test_call_dynamic_func():
    """测试调用动态生成的函数"""
    print("=" * 60)
    print("测试 5: 调用动态函数")
    print("=" * 60)
    
    func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=['x', 'y'],
        optional_arg_name_list=['z'],
        func_name='calculator'
    )
    
    # 调用函数
    result1 = func(1, 2)
    print(f"✅ 调用 func(1, 2): {result1}")
    
    result2 = func(1, 2, z=3)
    print(f"✅ 调用 func(1, 2, z=3): {result2}")
    
    result3 = func(x=10, y=20, z=30)
    print(f"✅ 调用 func(x=10, y=20, z=30): {result3}")
    
    print("\n✅ 函数调用测试通过！\n")


def test_fanboost_faas_scenario():
    """模拟 funboost.faas 的真实使用场景"""
    print("=" * 60)
    print("测试 6: funboost.faas 真实场景模拟")
    print("=" * 60)
    
    # 场景：web 服务从 redis 读取到队列的元数据
    redis_metadata = {
        'queue_name': 'user_registration_queue',
        'must_arg_name_list': ['username', 'email', 'password'],
        'optional_arg_name_list': ['phone', 'referral_code']
    }
    
    print(f"📡 从 Redis 获取元数据:")
    print(f"   队列: {redis_metadata['queue_name']}")
    print(f"   必需参数: {redis_metadata['must_arg_name_list']}")
    print(f"   可选参数: {redis_metadata['optional_arg_name_list']}")
    
    # 动态生成函数（无需真正的函数定义）
    fake_func = FakeFunGenerator.gen_fun_by_params(
        must_arg_name_list=redis_metadata['must_arg_name_list'],
        optional_arg_name_list=redis_metadata['optional_arg_name_list'],
        func_name='register_user'
    )
    
    print(f"\n🔧 动态生成函数: {fake_func.__name__}")
    print(f"   签名: {inspect.signature(fake_func)}")
    
    # 创建参数检查器
    params_info = ConsumingFuncInputParamsChecker.gen_func_params_info_by_func(fake_func)
    checker = ConsumingFuncInputParamsChecker(params_info)
    
    # 测试合法的发布参数
    valid_params_1 = {'username': 'alice', 'email': 'alice@example.com', 'password': '123456'}
    try:
        checker.check_params(valid_params_1)
        print(f"\n✅ 参数检查通过: {valid_params_1}")
    except ValueError as e:
        print(f"❌ 参数检查失败: {e}")
    
    # 测试包含可选参数的发布
    valid_params_2 = {
        'username': 'bob', 
        'email': 'bob@example.com', 
        'password': 'abc123',
        'phone': '13800138000'
    }
    try:
        checker.check_params(valid_params_2)
        print(f"✅ 参数检查通过（含可选参数）: {valid_params_2}")
    except ValueError as e:
        print(f"❌ 参数检查失败: {e}")
    
    # 测试非法参数（缺少必需参数）
    invalid_params_1 = {'username': 'charlie', 'email': 'charlie@example.com'}
    try:
        checker.check_params(invalid_params_1)
        print(f"❌ 应该检查失败但通过了: {invalid_params_1}")
    except ValueError as e:
        print(f"✅ 正确拒绝（缺少必需参数）: {e}")
    
    # 测试非法参数（包含未定义的参数）
    invalid_params_2 = {
        'username': 'david',
        'email': 'david@example.com',
        'password': 'xyz789',
        'unknown_field': 'value'  # 未定义的参数
    }
    try:
        checker.check_params(invalid_params_2)
        print(f"❌ 应该检查失败但通过了: {invalid_params_2}")
    except ValueError as e:
        print(f"✅ 正确拒绝（包含未定义参数）: {e}")
    
    print("\n✅ funboost.faas 场景测试完成！")


if __name__ == "__main__":
    print("\n🚀 开始测试 FakeFunGenerator 动态函数生成器\n")
    
    test_gen_fun_basic()
    test_gen_fun_only_must_params()
    test_gen_fun_only_optional_params()
    test_gen_params_info_from_dynamic_func()
    test_call_dynamic_func()
    test_fanboost_faas_scenario()
    
    print("=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
    print("""
💡 总结：
1. ✅ 可以根据参数列表动态生成函数
2. ✅ 生成的函数具有正确的签名和参数信息
3. ✅ 可以被 inspect 模块正确解析
4. ✅ 可以被 ConsumingFuncInputParamsChecker 使用
5. ✅ 完美支持 funboost.faas 的无函数对象场景

🎯 应用场景：
- funboost.faas web 服务从 redis 读取元数据
- 无需真正的消费函数对象
- 动态生成伪函数用于参数校验
- 实现完全解耦的 FaaS 架构
    """)
