from auto_run_on_remote import run_current_script_on_remote
# run_current_script_on_remote()
from funboost import boost,BrokerEnum



@boost('test_pulsar_topic2',broker_kind=BrokerEnum.PULSAR,qps=1,broker_exclusive_config={'subscription_name':'funboost_g1'},log_level=20)
def add(x,y):
    print(x+y)

if __name__ == '__main__':
    add.consume()