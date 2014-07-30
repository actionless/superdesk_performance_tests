from __future__ import unicode_literals

from base64 import b64encode
import requests

from locust import HttpLocust, TaskSet, task

HOSTNAME = 'https://master.sd-test.sourcefabric.org/api'

##############################################################################
# helpers:


def log_in(client):
    return client.post(
        HOSTNAME + '/auth/',
        {
            'username': 'admin',
            'password': 'admin',
        },
        verify=False,
    )


def encode_token(token):
    return b'basic ' + b64encode(token.encode('ascii') + b':')


auth = log_in(requests).json()
auth_token = encode_token(auth['token'])


def request_with_auth(l, method, uri, **kwargs):
    url = HOSTNAME + uri
    return l.client.request(
        method,
        url,
        headers={
            'authorization': auth_token,
        },
        verify=False,
    )

##############################################################################
# test itself:


class SuperdeskAuth(TaskSet):

    @task
    def log_in_and_out(self):
        test_auth = log_in(self.client).json()
        self.client.delete(
            HOSTNAME + '/auth/' + test_auth['_id'],
            headers={
                'authorization': encode_token(test_auth['token']),
            },
            verify=False,
            name='/api/auth/<id>'
        )


class SuperdeskWorkspace(TaskSet):

    @task
    def self_profile(self):
        request_with_auth(
            self,
            'GET',
            '/users/' + auth['user'],
        )

    @task
    def self_activity(self):
        request_with_auth(
            self,
            'GET',
            """/activity?embedded={"user":1}&max_results=50&sort=[('_created',-1)]""",
        )

    @task
    def list_ingest(self):
        request_with_auth(
            self,
            'GET',
            '/ingest',
        )

    @task
    def filter_ingest(self):
        request_with_auth(
            self,
            'GET',
            '/ingest?source={"query":{"match_all":{}},"size":10,"from":0}',
        )

    @task
    def list_notification(self):
        request_with_auth(
            self,
            'GET',
            '/notification',
        )


class SuperdeskTaskSet(TaskSet):
    tasks = {
        SuperdeskAuth: 1,
        SuperdeskWorkspace: 1,
    }


class SuperdeskPerformance(HttpLocust):
    task_set = SuperdeskTaskSet
    min_wait = 5000
    max_wait = 9000
