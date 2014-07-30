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


class TaskSetWithAuth(TaskSet):

    def request_with_auth(self, method, uri, **kwargs):
        url = HOSTNAME + uri
        headers = kwargs.pop('headers', {})
        headers.update({'authorization': auth_token})
        return self.client.request(
            method,
            url,
            headers=headers,
            verify=False,
            **kwargs
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


class SuperdeskArchive(TaskSetWithAuth):

    @task
    def archive_page(self):
        self.request_with_auth(
            'GET',
            '/archive?source={"query":{"match_all":{}},'
            '"size":25,"from":0,"sort":[{"versioncreated":"desc"}]}',
        )


class SuperdeskWorkspace(TaskSetWithAuth):

    @task
    def self_profile(self):
        self.request_with_auth(
            'GET',
            '/users/' + auth['user'],
        )

    @task
    def self_activity(self):
        self.request_with_auth(
            'GET',
            '/activity?embedded={"user":1}'
            "&max_results=50&sort=[('_created',-1)]",
        )

    @task
    def list_ingest(self):
        self.request_with_auth(
            'GET',
            '/ingest',
        )

    @task
    def filter_ingest(self):
        self.request_with_auth(
            'GET',
            '/ingest?source={"query":{"match_all":{}},"size":10,"from":0}',
        )

    @task
    def list_notification(self):
        self.request_with_auth(
            'GET',
            '/notification',
        )


class SuperdeskTaskSet(TaskSet):
    tasks = {
        SuperdeskAuth: 1,
        SuperdeskWorkspace: 1,
        SuperdeskArchive: 1,
    }


class SuperdeskPerformance(HttpLocust):
    task_set = SuperdeskTaskSet
    min_wait = 5000
    max_wait = 9000
