from namely import Namely
from okta import Okta
from interface import Interface
from pdb import set_trace

CONFIG_OBJECT = {
    'dept_and_title_only': True,
    'skip_first_name': True,
    'black_set': {},
    'email_white_list': [],
    'alert': False
}

RUN_CONFIG = {
    'onboarding': False,
    'reconcile': False,
}

if __name__ == '__main__':
    namely, okta = Namely(), Okta()
    interface = Interface(namely, okta, CONFIG_OBJECT)
    employee_res = interface.onboard_new_employees()
    reconcile_res = interface.reconcile_differences()
