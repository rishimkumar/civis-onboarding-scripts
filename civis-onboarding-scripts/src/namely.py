import requests
import os

from pdb import set_trace
from urllib.parse import urlencode, urljoin
from math import ceil
from os.path import exists
import json

class Namely():
    ROOT = 'https://civisanalytics.namely.com/api/v1'
    CACHE_URL = 'namely_profiles.json'
    def __init__(self):
        """
        session is an authenciated requests session
        users is a list of all users from the namely api
        """
        self.session = Namely.setup_auth()
        self.users = self.get_user_profiles()

    @staticmethod
    def setup_auth():
        """
        creates an authenticated requests sessions
        """

        s = requests.Session()
        s.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ["NAMELY_API_KEY"]}',
        })

        return s

    @staticmethod
    def get_cached_file():
        """
        When working locally pulls a cached file of namely users.
        """
        if not exists(Namely.CACHE_URL):
            return [], False

        with open(Namely.CACHE_URL, 'r') as infile:
            return json.load(infile), True

    def user_urls(self):
        """
        Builds a list of the urls needed to get all user profiles from namely api.
        """
        res = self.session.get(f'{Namely.ROOT}/profiles')
        count = res.json()['meta']['total_count']
        pages = ceil(count / 50)
        build_url = lambda i: '{}/profiles?{}'.format(Namely.ROOT, urlencode({"page": i, "per_page": 50}))
        urls = [build_url(i) for i in range(1, pages + 1)]

        return urls

    def get_user_profiles(self):
        """
        Grabs all users from namely api.
        """
        data, ok = Namely.get_cached_file()
        if ok:
            return data

        urls = self.user_urls()

        get_user_profile = lambda url: self.session.get(url).json()['profiles']

        users = [get_user_profile(url) for url in urls]
        flattened_users = sum(users, [])

        return flattened_users

    @staticmethod
    def get_dept_from_namely_info(namely_info):
        is_city = lambda x: x['name'].lower() in {'chicago', 'dc'}
        dept_obj = [item for item in namely_info['links']['groups'] if not is_city(item)].pop()
        return dept_obj['name']

    @staticmethod
    def extract_profile_info(namely_info):
        commons_keys = {
            'first_name',
            'preferred_name',
            'last_name',
            'email'
        }

        d = {key:namely_info[key] for key in commons_keys}


        d.update({
            'department': Namely.get_dept_from_namely_info(namely_info),
            'title': namely_info['links']['job_title']['title']
        })

        return d

    @staticmethod
    def convert_namely_info_to_okta(namely_info):
        return {
            'lastName': namely_info['last_name'],
            'firstName': namely_info['preferred_name'] or namely_info['first_name'],
            'email': namely_info['email'],
            'login': namely_info['email'],
            'department': namely_info['department'],
            'title': namely_info['title']
        }

if __name__ == '__main__':
    namely = Namely()
