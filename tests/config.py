import unittest
import os

import vcr
from dotenv import load_dotenv

import wikirate4py

load_dotenv()
username = os.environ.get('API_USERNAME', '')
password = os.environ.get('API_PASSWORD', '')
bearer_token = os.environ.get('BEARER_TOKEN', '')
wikirate_api_url = os.environ.get('API_URL', '')
use_replay = os.environ.get('USE_REPLAY', True)

tape = vcr.VCR(
    cassette_library_dir='../cassettes',
    filter_headers=['Authorization', 'X-API-Key'],
    serializer='json',
    record_mode='once' if use_replay else 'all',
)


class Wikirate4PyTestCase(unittest.TestCase):

    def setUp(self):
        self.auth = (username, password)
        self.api = wikirate4py.API(oauth_token=bearer_token,
                                   wikirate_api_url=wikirate_api_url,
                                   auth=self.auth)
