from __future__ import unicode_literals

from base64 import b64encode
import requests
import json

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

    def request_with_auth(self, method, uri, json_data=None, **kwargs):
        url = HOSTNAME + uri
        headers = kwargs.pop('headers', {})
        headers.update({'authorization': auth_token})
        if json_data:
            kwargs['data'] = json.dumps(json_data)
            headers.update({
                "content-type": "application/json;charset=UTF-8"
            })
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
            name='/api/auth/{$AUTH_ID}',
            headers={
                'authorization': encode_token(test_auth['token']),
            },
            verify=False
        )


class SuperdeskArchive(TaskSetWithAuth):

    @task
    def archive_page(self):
        self.request_with_auth(
            'GET',
            '/archive?source={"query":{"match_all":{}},'
            '"size":25,"from":0,"sort":[{"versioncreated":"desc"}]}',
        )


class SuperdeskUserProfile(TaskSetWithAuth):

    @task
    def self_profile(self):
        self.request_with_auth(
            'GET',
            '/users/' + auth['user'],
        )


class SuperdeskWorkspace(TaskSetWithAuth):
    tasks = {SuperdeskUserProfile: 1}

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


class SuperdeskAuthoring(TaskSetWithAuth):
    tasks = {SuperdeskUserProfile: 1}

    def create_item(self):
        self.item_id = self.request_with_auth(
            'POST',
            '/archive',
            json_data={
                "type": "text",
            },
        ).json()['_id']

    def edit_item(self, new_text):
        self.request_with_auth(
            'PATCH',
            '/archive/' + self.item_id,
            name='/api/archive/{$ITEM_ID}',
            json_data={
                "body_html": "<p>{text}</p>".format(text=new_text)
            },
        )

    def item_history(self):
        self.request_with_auth(
            'GET',
            '/archive/' + self.item_id,
            name='/api/archive/{$ITEM_ID}',
        )
        self.request_with_auth(
            'GET',
            '/archive/' + self.item_id +
            '?version=all&embedded={"user":1}',
            name='/api/archive/{$ITEM_ID}?version=all&embedded={"user":1}',
        )

    def delete_item(self):
        self.request_with_auth(
            'DELETE',
            '/archive/' + self.item_id,
            name='/api/archive/{$ITEM_ID}'
        )

    @task
    def authoring_cycle(self):
        self.create_item()
        for i in range(20):
            self.edit_item(str(i))
        self.item_history()
        self.delete_item()


class SuperdeskTaskSet(TaskSet):
    tasks = {
        SuperdeskAuth: 1,
        SuperdeskWorkspace: 10,
        SuperdeskArchive: 100,
        SuperdeskAuthoring: 50,
    }


class SuperdeskPerformance(HttpLocust):
    task_set = SuperdeskTaskSet
    min_wait = 1
    max_wait = 10000  # 10 seconds
