from __future__ import unicode_literals

from locust import HttpLocust, TaskSet, task

URL = 'http://nodejs-dev.sourcefabric.org/'


class EmbedPinger(TaskSet):

    def embed_get(self, backend_hostname):
        for limit in range(2, 22+1):
            self.client.get(
                URL,
                params={
                    'liveblog.servers.rest': backend_hostname,
                    'liveblog.limit': limit,
                }
            )

##############################################################################
# test itself:


class RpTaskSet(EmbedPinger):

    @task
    def test_embed(self):
        self.embed_get('rp.superdesk.pro')


class TwTaskSet(EmbedPinger):

    @task
    def test_embed(self):
        self.embed_get('tw.superdesk.pro')


class LiveBlogTaskSet(TaskSet):
    tasks = {
        RpTaskSet: 1,
        TwTaskSet: 1,
    }


class SuperdeskPerformance(HttpLocust):
    task_set = LiveBlogTaskSet
    min_wait = 1
    max_wait = 30000  # 10 seconds
