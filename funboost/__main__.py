import fire

from funboost.core.cli.funboost_fire import check_pass_params, BoosterFire


def main():
    check_pass_params()
    fire.Fire(BoosterFire, )

if __name__ == '__main__':
    main()