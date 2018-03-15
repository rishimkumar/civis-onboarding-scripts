from pdb import set_trace
from namely import Namely
from okta import Okta
from copy import deepcopy
import pprint
import logging

class Interface():
    def __init__(self, namely, okta, config):
        self.namely = namely
        self.okta = okta
        self.config = config

    def diff_email_set(self, namely_users, okta_users):
        """
        Returns set of active users present in namely not present in okta.
        """
        logging.info('Fetching set of active users present  in namely and not present in okta')
        active_namely_employees = [x for x in namely_users if x['user_status'] == 'active']
        active_okta_employees = [x for x in okta_users if x['status'] in {'ACTIVE', 'PROVISIONED'}]

        namely_emails = {x['email'] for x in active_namely_employees}
        okta_emails = {x['profile']['email'] for x in active_okta_employees}

        return namely_emails - okta_emails

    def email_to_namely_profiles(self, namely_users, email_set):
        """
        Maps namely email to a user profile.
        """
        profiles = [user for user in namely_users if user['email'] in email_set]

        if len(profiles) != len(email_set):
            raise Exception(f'Expecting profile list of {len(email_set)}, got {len(profile)}')

        return profiles

    def onboard_new_employees(self):
        """
        Takes all employees not in Okta and creates their accounts.
        """

        print ("ONBOARDING NEW EMPLOYEES...")

        pp = pprint.PrettyPrinter(indent=4)
        difference_emails = self.diff_email_set(self.namely.users, self.okta.users)

        print ("LOOKING FOR OKTA/NAMELY DIFFERENCES...")

        if not difference_emails:
            print ('Okta and Namely up to date!')

        namely_profiles = self.email_to_namely_profiles(self.namely.users, difference_emails)


        if not namely_profiles:
            print ('No additional users detected')
            return

        verb = 'Created' if self.config['alert'] else 'Detected'
        profiles = {}
        for idx, namely_profile in enumerate(namely_profiles):
            email = namely_profile['email']



            if len(self.config['email_white_list']) > 0 and (email not in self.config['email_white_list']):
                print ("Skipping {} because not in white list".format(email))
                continue


            print ('Employee {} is present in namely not present in Okta'.format(email))
            if self.config['alert']:
                print ('Not attempting to create because on alert only mode')
                print('\n' * 3)
                continue

            print ('Attempting to create...')
            res, ok = self.okta.create_new_user(namely_profile)
            if ok:
                profiles[email] = res

            if idx != len(namely_profiles) - 1:
                print('\n' * 3)

        return profiles

    def bucket_by_email(self):
        namely_by_email = {x["email"]: x for x in self.namely.users}
        okta_by_email = {x['profile']['email']: x for x in self.okta.users}

        common_to_both = namely_by_email.keys() & okta_by_email.keys()

        common = lambda x: (x['email'] if 'email' in x else x['profile']['email']) in common_to_both
        namely_by_email = {x["email"]: x for x in self.namely.users if common(x)}
        okta_by_email = {x['profile']['email']: x for x in self.okta.users if common(x)}

        return namely_by_email, okta_by_email, common_to_both

    @staticmethod
    def compare_okta_and_namely_profile(namely, okta):

        namely_proile = Namely.extract_profile_info(namely)
        as_okta = Namely.convert_namely_info_to_okta(namely_proile)

        okta_profile = okta['profile']
        diffs = {}

        for (namely_key, namely_value) in as_okta.items():
            okta_value = okta_profile.get(namely_key)
            if okta_value != namely_value:
                diffs[namely_key] = {
                    'namely': namely_value,
                    'okta': okta_value
                }
        return diffs

    def diff_okta_and_namely_profiles(self):
        """
        """
        namely_emails, okta_emails, common = self.bucket_by_email()

        diff_total = {}

        for email in common:

            namely_profile, okta_profile = namely_emails[email], okta_emails[email]

            diffs = Interface.compare_okta_and_namely_profile(namely_profile, okta_profile)
            if len(diffs):
                diff_total[email] = diffs
        return diff_total

    def select_keys(self, difference_object):
        all_keys = difference_object.keys()

        if self.config['dept_and_title_only']:
            return all_keys & {'department', 'title'}

        if self.config['skip_first_name']:
            return all_keys - {'firstName'}

        return all_keys

    def process_diference_object(self, difference_object):
        selected_keys = self.select_keys(difference_object)
        return {k:v['namely'] for k,v in difference_object.items() if k in selected_keys}

    def reconcile_differences(self):
        print ("LOOKING FOR PROFILE DIFFERENCES BETWEEN NAMELY AND OKTA...")
        difference_objects = self.diff_okta_and_namely_profiles()
        if not difference_objects:
            print ("NO DIFFERENCES FOUND")
            return {}

        email_to_okta = self.okta.email_user_map()
        pp = pprint.PrettyPrinter(indent=4)

        changes = {}

        for idx, (email, difference_object) in enumerate(difference_objects.items()):
            update_object = self.process_diference_object(difference_object)

            last_item = idx == len(difference_objects) - 1

            if len(self.config['email_white_list']) > 0 and email not in self.config['email_white_list']:
                print ("Skipping {} because not in white list".format(email))
                continue

            okta_user = email_to_okta[email]
            okta_id = okta_user['id']
            changes[email] = update_object
            print ('Processing information for {}...'.format(email))

            if self.config['alert']:
                pp.pprint('Following differences detected for {}\'s profile'.format(email))
                pp.pprint(update_object)
                if not last_item:
                    print('\n' * 3)
                continue

            res = self.okta.update_user(okta_id, update_object)
            pp.pprint('Updated {}\'s okta profile with the following changes'.format(email))
            pp.pprint(update_object)

            if not last_item:
                print('\n' * 3)

        return changes
