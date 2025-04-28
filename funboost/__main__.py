import sys

import fire
from funboost.core.cli.funboost_fire import BoosterFire, env_dict


def _check_pass_params():
    has_passing_arguments_project_root_path = False
    for a in sys.argv:
        if '--project_root_path=' in a:
            has_passing_arguments_project_root_path = True
            project_root_path = a.split('=')[-1]
            sys.path.insert(1, project_root_path)
            env_dict['project_root_path'] = project_root_path
    if has_passing_arguments_project_root_path is False:
        raise Exception('命令行没有传参 --project_root_path=')


def main():
    _check_pass_params()
    

    fire.Fire(BoosterFire, )


if __name__ == '__main__':
    main()

'''
python -m funboost  --project_root_path=/codes/funboost   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  show_all_queues

python -m funboost  --project_root_path=/codes/funboost   --booster_dirs_str=test_frame/test_funboost_cli/test_find_boosters --max_depth=2  push test_find_queue1 --x=1 --y=2


python -m funboost  --project_root_path=/codes/funboost  start_web
'''
