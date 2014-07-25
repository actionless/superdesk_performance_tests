from __future__ import unicode_literals

from base64 import b64encode

from locust import HttpLocust, TaskSet, task

HOSTNAME = 'https://master.sd-test.sourcefabric.org/api'


def log_in(l):
    return l.client.post(
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
            b'basic ' + b64encode(l.auth['token'].encode('ascii') + b':'),
        }
    )


class SuperdeskLogIn(TaskSet):
    tasks = {
        log_in: 1
    }


class SuperdeskProfile(TaskSet):
    def on_start(self):
        self.auth = log_in(self).json()

    @task
    def self_profile(self):
        request_with_auth(
            self, 'GET',
            '/users/' + self.auth['user'],
        )


class SuperdeskTaskSet(TaskSet):
    tasks = {
        SuperdeskLogIn: 1,
        SuperdeskProfile: 1,
    }


class SuperdeskPerformance(HttpLocust):
    task_set = SuperdeskTaskSet
    min_wait = 5000
    max_wait = 9000
