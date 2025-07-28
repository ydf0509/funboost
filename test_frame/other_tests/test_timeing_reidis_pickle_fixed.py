import pickle
import codecs

# 原始的二进制数据
s1 = b'''
\x80\x04\x95W\x04\x00\x00\x00\x00\x00\x00}\x94(\x8c\x07version\x94K\x01\x8c\x02id\x94\x8c\x09cron_job1\x94\x8c\x04func\x94\x8c=funboost.timing_job.timing_job_base:push_fun_params_to_broker\x94\x8c\x07trigger\x94\x8c\x19apscheduler.triggers.cron\x94\x8c\x0BCronTrigger\x94\x93\x94)\x81\x94}\x94(h\x01K\x02\x8c\x08timezone\x94\x8c\x04pytz\x94\x8c\x02_p\x94\x93\x94(\x8c\x0DAsia/Shanghai\x94M\xE8qK\x00\x8c\x03LMT\x94t\x94R\x94\x8c\x0Astart_date\x94N\x8c\x08end_date\x94N\x8c\x06fields\x94]\x94(\x8c apscheduler.triggers.cron.fields\x94\x8c\x09BaseField\x94\x93\x94)\x81\x94}\x94(\x8c\x04name\x94\x8c\x04year\x94\x8c\x0Ais_default\x94\x88\x8c\x0Bexpressions\x94]\x94\x8c%apscheduler.triggers.cron.expressions\x94\x8c\x0DAllExpression\x94\x93\x94)\x81\x94}\x94\x8c\x04step\x94Nsbaubh\x18\x8c\x0AMonthField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8c\x05month\x94h\x1F\x88h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x18\x8c\x0FDayOfMonthField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8c\x03day\x94h\x1F\x88h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x18\x8c\x09WeekField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8c\x04week\x94h\x1F\x88h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x18\x8c\x0EDayOfWeekField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8c\x0Bday_of_week\x94h\x1F\x89h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x1A)\x81\x94}\x94(h\x1D\x8c\x04hour\x94h\x1F\x89h ]\x94h"\x8c\x0FRangeExpression\x94\x93\x94)\x81\x94}\x94(h'N\x8c\x05first\x94K\x17\x8c\x04last\x94K\x17ubaubh\x1A)\x81\x94}\x94(h\x1D\x8c\x06minute\x94h\x1F\x89h ]\x94hM)\x81\x94}\x94(h'NhPK1hQK1ubaubh\x1A)\x81\x94}\x94(h\x1D\x8c\x06second\x94h\x1F\x89h ]\x94hM)\x81\x94}\x94(h'NhPK2hQK2ubaube\x8c\x06jitter\x94Nub\x8c\x08executor\x94\x8c\x07default\x94\x8c\x04args\x94\x8c\x0Asum_queue3\x94\x85\x94\x8c\x06kwargs\x94}\x94(\x8c\x01x\x94K2\x8c\x01y\x94K<uh\x1D\x8c.push_fun_params_to_broker_for_queue_sum_queue3\x94\x8c\x12misfire_grace_time\x94K\x01\x8c\x08coalesce\x94\x88\x8c\x0Dmax_instances\x94K\x01\x8c\x0Dnext_run_time\x94\x8c\x08datetime\x94\x8c\x08datetime\x94\x93\x94C\x0A\x07\xE9\x06\x1A\x1712\x00\x00\x00\x94h\x0F(h\x10M\x80pK\x00\x8c\x03CST\x94t\x94R\x94\x86\x94R\x94u.
'''

def analyze_pickle_data():
    """分析 pickle 数据的问题"""
    print("=== 分析 pickle 数据 ===")
    
    # 1. 检查原始数据
    print(f"原始数据长度: {len(s1)}")
    print(f"数据开头几个字节: {s1[:20]}")
    print(f"数据结尾几个字节: {s1[-20:]}")
    
    # 2. 清理数据：移除开头和结尾的换行符
    cleaned_data = s1.strip()
    print(f"清理后数据长度: {len(cleaned_data)}")
    print(f"清理后开头几个字节: {cleaned_data[:20]}")
    print(f"清理后结尾几个字节: {cleaned_data[-20:]}")
    
    # 3. 尝试反序列化清理后的数据
    try:
        job = pickle.loads(cleaned_data)
        print("✅ 反序列化成功!")
        print(f"Job 类型: {type(job)}")
        print(f"Job 内容: {job}")
        return job
    except Exception as e:
        print(f"❌ 反序列化失败: {e}")
        return None

def fix_redis_pickle_issue():
    """修复 Redis pickle 序列化问题的方案"""
    print("\n=== Redis Pickle 问题修复方案 ===")
    
    print("""
    这个问题的原因和解决方案：
    
    1. 问题原因：
       - 二进制数据前后包含了换行符等额外字符
       - pickle.loads() 对数据格式要求严格，不能有额外的字符
       - 可能是从 Redis 或文件中读取时引入了额外字符
    
    2. 解决方案：
       a) 数据清理方法：
          - 使用 data.strip() 移除前后空白字符
          - 检查数据完整性
       
       b) Redis 存储改进：
          - 确保存储时使用正确的序列化方法
          - 读取时正确处理二进制数据
       
       c) APScheduler 配置优化：
          - 使用合适的序列化器配置
          - 确保 jobstore 配置正确
    """)

def create_test_job():
    """创建一个测试 job 来验证序列化/反序列化"""
    print("\n=== 创建测试 job ===")
    
    try:
        from apscheduler.job import Job
        from apscheduler.triggers.cron import CronTrigger
        import datetime
        import pytz
        
        # 创建一个简单的测试 job
        trigger = CronTrigger(hour=23, minute=49, second=50, timezone=pytz.timezone('Asia/Shanghai'))
        
        job_data = {
            'version': 1,
            'id': 'test_job',
            'func': 'funboost.timing_job.timing_job_base:push_fun_params_to_broker',
            'trigger': trigger,
            'executor': 'default',
            'args': ('test_queue',),
            'kwargs': {'x': 1, 'y': 2},
            'name': 'test_push_job',
            'misfire_grace_time': 1,
            'coalesce': True,
            'max_instances': 1,
            'next_run_time': datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        }
        
        # 测试序列化
        pickled = pickle.dumps(job_data)
        print(f"✅ 序列化成功，数据长度: {len(pickled)}")
        
        # 测试反序列化
        unpickled = pickle.loads(pickled)
        print(f"✅ 反序列化成功: {unpickled['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == '__main__':
    # 分析现有数据
    job = analyze_pickle_data()
    
    # 提供修复方案
    fix_redis_pickle_issue()
    
    # 创建测试案例
    create_test_job()
    
    print("\n=== 建议 ===")
    print("""
    1. 立即修复：对现有数据使用 data.strip() 清理
    2. 长期方案：检查 Redis 存储逻辑，确保数据存储时不包含额外字符
    3. 预防措施：在存储和读取时都进行数据验证
    """) 