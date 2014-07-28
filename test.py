from __future__ import unicode_literals

from base64 import b64encode
import requests

from locust import HttpLocust, TaskSet, task

HOSTNAME = 'https://master.sd-test.sourcefabric.org/api'


def log_in(client):
    return client.post(
        HOSTNAME + '/auth/',
        {
            'username': 'admin',
            'password': 'admin',
        },
        verify=False,
    )


def request_with_auth(l, method, uri, **kwargs):
    url = HOSTNAME + uri
    return l.client.request(
        method,
        url,
        headers={
            'authorization':
            b'basic ' + b64encode(auth['token'].encode('ascii') + b':'),
        },
        verify=False,
    )


auth = log_in(requests).json()


class SuperdeskAuth(TaskSet):

    @task
    def log_in_and_out(self):
        auth = log_in(self.client).json()
        self.client.delete(
            HOSTNAME + '/auth/' + auth['_id'],
            verify=False,
            name='/api/auth/<id>'
        )


class SuperdeskProfile(TaskSet):

    @task
    def self_profile(self):
        request_with_auth(
            self, 'GET',
            '/users/' + auth['user'],
        )


class SuperdeskTaskSet(TaskSet):
    tasks = {
        SuperdeskAuth: 1,
        SuperdeskProfile: 1,
    }


class SuperdeskPerformance(HttpLocust):
    task_set = SuperdeskTaskSet
    min_wait = 5000
    max_wait = 9000
