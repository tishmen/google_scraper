import random
import time

from urllib.parse import urlparse, parse_qs

import htmlmin
import requests

from bs4 import BeautifulSoup

from django.conf import settings


class GoogleParser(object):

    '''parse response from google'''

    def __init__(self, response):
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def parse_links(self):
        '''return result nodes that contain snippet node'''
        return [node.parent for node in self.soup.select('.g .s')]

    def parse_url(self, node):
        '''return title url from result node'''
        return parse_qs(urlparse(node.a['href']).query)['q'][0]

    def parse_title(self, node):
        '''return title text from result node'''
        return node.a.get_text()

    def parse_snippet(self, node):
        '''return snippet text from result node'''
        return node.select_one('.st').get_text()

    def parse_link(self, node):
        '''return parsed link dictionary'''
        return {
            'url': self.parse_url(node),
            'title': self.parse_title(node),
            'snippet': self.parse_snippet(node),
        }

    def parse_next_page(self):
        '''return next page url or None'''
        return 'https://www.google.com' + \
            self.soup.find('span', string='Next').find_previous('a')['href']

    def get_html(self):
        '''return minifyfied html from soup'''
        return htmlmin.minify(str(self.soup))

    def get_links(self):
        '''return parsed link dictionaries'''
        links = []
        for node in self.parse_links():
            links.append(self.parse_link(node))
        return links

    def get_next_page(self):
        '''return next page url or None'''
        try:
            return self.parse_next_page()
        except IndexError:
            pass


class GoogleScraper(object):

    '''follow next page and extract links'''

    def __init__(self, search, user_agent=None, proxy=None):
        self.success = None
        self.url = search.url
        self.search_result_count = 0
        self.page_result_count = 0
        self.start = 1
        self.search = search
        self.user_agent = user_agent
        self.proxy = proxy

    def sleep(self, seconds):
        '''sleep n seconds'''
        print('sleeping for {} seconds'.format(seconds))
        time.sleep(seconds)

    def update_proxy(self):
        '''update proxy for instance'''
        from .models import Proxy
        old_proxy = self.proxy
        self.proxy = Proxy.get_proxy()
        print('switching proxy from {} to {}'.format(old_proxy, self.proxy))
        self.sleep(
            random.uniform(
                settings.MIN_REQUEST_SLEEP, settings.MAX_REQUEST_SLEEP
            )
        )

    def get_request_params(self):
        '''return request call parameters to be unpacked.'''
        params = {'url': self.url, 'timeout': settings.REQUEST_TIMEOUT}
        if self.user_agent:
            params['headers'] = {'User-Agent': self.user_agent}
        if self.proxy:
            params['proxies'] = {
                'http': 'http://{}:{}'.format(self.proxy.host, self.proxy.port)
            }
        return params

    def get_response(self):
        '''fetch http response for url'''
        if self.proxy:
            self.proxy.register()
            response = requests.get(**self.get_request_params())
            self.proxy.unregister()
        else:
            response = requests.get(**self.get_request_params())
        print('got response from url {}'.format(self.url))
        if self.proxy:
            self.proxy.set_online()
        return response

    def handle_response(self):
        '''return http response for url or None.'''
        try:
            return self.get_response()
        except requests.ConnectionError as e:
            print('connection failed {}'.format(e))
        except requests.Timeout as e:
            print('connection timeout {}'.format(e))
        if self.proxy:
            self.proxy.unset_online()
            self.update_proxy()
        print('failed to get response from url {}'.format(self.url))

    def handle_status_code(self):
        '''return http response or None if status code not equal to 200'''
        if self.response.status_code == 200:
            print('status code 200 for {}'.format(self.url))
            if self.proxy:
                self.proxy.unset_google_ban()
            return self.response
        print(
            'bad status code {} for {}'.format(
                self.response.status_code, self.url
            )
        )
        if self.proxy:
            self.proxy.set_google_ban()
            self.update_proxy()

    def do_request(self):
        '''perform http request and handle exceptions'''
        for i in range(settings.MAX_RETRY):
            self.response = self.handle_response()
            if not self.response:
                print('retrying for {} time'.format(i + 1))
                continue
            self.response = self.handle_status_code()
            if not self.response:
                print('retrying for {} time'.format(i + 1))
                continue
            self.parser = GoogleParser(self.response)
            break

    def get_links(self):
        '''get link array from parser and adjust result count'''
        self.links = self.parser.get_links()
        self.page_result_count = len(self.links)

    def get_end(self):
        '''return end result index'''
        return self.start + self.page_result_count

    def create_page(self):
        '''create GooglePage entry in database'''
        from .models import GooglePage
        self.page = GooglePage.objects.create(
            search=self.search,
            url=self.url,
            html=self.parser.get_html(),
            result_count=self.page_result_count,
            start=self.start,
            end=self.get_end(),
            next_page=self.parser.get_next_page()
        )
        print('created google page {}'.format(self.page))

    def create_links(self):
        '''create GoogleLink entries in database'''
        from .models import GoogleLink
        links = []
        for i, link_params, in enumerate(self.links):
            link_params.update({'page': self.page, 'rank': self.start + i})
            link = GoogleLink.objects.create(**link_params)
            print('created google link {}'.format(link))
            links.append(link)
        self.links = links
        print(
            'created {} google links for google page {}'.format(
                len(self.links), self.page
            )
        )

    def is_request_failed(self):
        '''check for valid response'''
        if self.response:
            return False
        self.success = False
        return True

    def is_last_page(self):
        '''check if we are on last page of search results'''
        if self.page.next_page:
            return
        print('reached last page for query {}'.format(self.search))
        self.success = True
        return True

    def update_loop(self):
        '''update instance with new values'''
        self.url = self.page.next_page
        self.search_result_count += self.page_result_count
        self.start = self.get_end()
        self.success = True
        self.sleep(
            random.uniform(settings.MIN_RETRY_SLEEP, settings.MAX_RETRY_SLEEP)
        )

    def update_search(self):
        '''update search record with new values'''
        self.search.set_result_count(self.search_result_count)
        self.search.set_success(self.success)

    def scrape(self):
        '''main scrape call'''
        print('scraping for query {}'.format(self.search))
        for _ in range(settings.MAX_PAGE):
            self.do_request()
            if self.is_request_failed():
                break
            self.get_links()
            self.create_page()
            self.create_links()
            if self.is_last_page():
                break
            self.update_loop()
        self.update_search()
