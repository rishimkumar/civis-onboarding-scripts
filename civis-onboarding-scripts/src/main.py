from namely import Namely
from okta import Okta
from interface import Interface
from pdb import set_trace
from os import getenv
import logging


def get_bool_env(x, default):
    res = getenv(x)
    if res:
        return res.lower() == 'true'
    return default


def get_list_env(x):

    if not x:
        return []

    return x.split(",")


CONFIG_OBJECT = {
    'dept_and_title_only': get_bool_env('DEPT_AND_TITLE', False),
    'skip_first_name': get_bool_env('DEPT_AND_TITLE', True),
    'black_set': get_list_env('BLACK_LIST'),
    'email_white_list': [],  # get_list_env('WHITE_LIST'),
    'alert': get_bool_env('ALERT', True)
}

RUN_CONFIG = {
    'onboarding': get_bool_env('ONBOARDING', True),
    'reconcile': get_bool_env('RECONCILE', True),
}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='/tmp/myapp.log',
                        filemode='w')
    namely, okta = Namely(), Okta()
    interface = Interface(namely, okta, CONFIG_OBJECT)

    if RUN_CONFIG['onboarding']:
        employee_res = interface.onboard_new_employees()

    if RUN_CONFIG['reconcile']:
        reconcile_res = interface.reconcile_differences()
