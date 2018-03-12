import os
import requests
from pdb import set_trace
from namely import Namely
import pprint
import json

pp = pprint.PrettyPrinter(indent=4)

class Okta():
    ROOT = 'https://civisanalytics.okta.com/api/v1'
    def __init__(self):
        """
        session is an authenticated session
        groups is list of all groups
        users is of all user profiles
        """
        self.session = Okta.setup_auth()
        self.groups = self.get_groups()
        self.users = self.get_user_profiles()

    @staticmethod
    def setup_auth():
        """
        Authenticates a user
        """
        s = requests.Session()
        s.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'SSWS {os.environ["OKTA_API_KEY"]}',
        })

        return s

    def get_user_profiles(self):
        """
        grabs list of user profiles
        """
        res = self.session.get(f'{Okta.ROOT}/users')
        return res.json()

    def create_new_user(self, namely_info):
        """
        takes a namely_info and creates a new user profile
        """
        title = namely_info['job_title']['title']

        dept = Namely.get_dept_from_namely_info(namely_info)

        groups = Okta.assign_groups(dept, title)

        groupIds = [self.groups[group_name]['id'] for group_name in groups]

        data = {
            "profile": {
                "firstName": namely_info['preferred_name'] or namely_info['first_name'],
                "lastName": namely_info['last_name'],
                "email": namely_info['email'],
                "login": namely_info['email'],
                "department": dept
            },
            "groupIds": groupIds
        }

        pp = pprint.PrettyPrinter(indent=4)
        print ('{} is associated with following groups {}'.format(
            data['profile']['email'],
            ' '.join(sorted(list(groups)))
        ))
        pp.pprint(data)


        res = self.session.post(f'{Okta.ROOT}/users',
                          data = json.dumps(data),
                          params = {'activate': 'false'})
        if res.ok:
            print('Creation was successful')
            return data, True

        else:
            print(f'Creation failed due to {res.reason} with {res.status_code}')

            return {}, False

    @staticmethod
    def assign_groups(dept, title):
        """
        takes a dept and title and outputs a list of groups
        """
        groups = {'All Staff', 'Everyone'}
        depts = {
            'Operations': 'Operations',
            'Applied Data Science': 'ADS',
            'Tech':'Tech',
            'Data Science Research and Development': 'DS R&D',
            'Sales & Client Success': 'Client Success'
        }

        if dept in depts:
            groups.add(dept)

        return groups

    def set_dept(self, user_id, dept):
        """
        update dept for a user
        """

        payload = {'profile': dept}
        marshalled = json.dumps(payload)
        res = self.session.post(f'{Okta.ROOT}/users/{user_id}', data = marshalled)

    def update_user(self, user_id, okta_profile):
        """
        update dept for a user
        """

        payload = {'profile': okta_profile}
        marshalled = json.dumps(payload)
        res = self.session.post(f'{Okta.ROOT}/users/{user_id}', data = marshalled)
        return res

    def get_groups(self):
        """
        grabs all groups from namely
        """
        res = self.session.get(f'{Okta.ROOT}/groups/')
        json =  res.json()
        return {x['profile']['name']: x for x in json}

    def email_user_map(self):
        """
        maps user emails to okta profiles
        """
        return {x['profile']['email']: x for x in self.users}

if __name__ == '__main__':
    okta = Okta()
