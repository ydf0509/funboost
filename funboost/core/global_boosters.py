import os
import nb_log

logger = nb_log.get_logger(__name__)

pid_queue_name__booster_map = {}
queue_name__boost_params_consuming_function_map = {}


def regist_booster(queue_name: str, booster):
    pid_queue_name__booster_map[(os.getpid(), queue_name)] = booster
    queue_name__boost_params_consuming_function_map[queue_name] = (booster.boost_params, booster.consuming_function)


def show_all_boosters():
    queues = []
    for pid_queue_name, booster in pid_queue_name__booster_map.items():
        queues.append(pid_queue_name[1])
        logger.debug(f'booster: {pid_queue_name[1]}  {booster}')
    logger.info(f'queues: {queues}')
