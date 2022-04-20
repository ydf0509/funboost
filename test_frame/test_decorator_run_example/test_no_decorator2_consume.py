
from funboost import boost
from nb_log.nb_log_config_default import computer_ip

def add(x,y):
    print(x+y)


add_boost = boost(f'{computer_ip.replace(".","_")}__add_queue',qps=3)(add)

print(add_boost.queue_name)

add_boost.consume()