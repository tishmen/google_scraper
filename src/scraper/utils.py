import time

from urllib.parse import urlparse, parse_qs

import requests

from bs4 import BeautifulSoup

from django.conf import settings


class GoogleParser(object):

    '''parses the response from google'''

    def __init__(self, response):
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def parse_next_page(self):
        '''returns next page url or exception'''
        return 'https://www.google.com' + \
            self.soup.select('.b > .fl')[0]['href']

    def parse_links(self):
        '''returns result nodes that contain snippet node'''
        return [node.parent for node in self.soup.select('.g .s')]

    def parse_title(self, node):
        '''returns title text from result node'''
        return node.a.get_text()

    def parse_snippet(self, node):
        '''returns snippet text from result node'''
        return node.select_one('.st').get_text()

    def parse_url(self, node):
        '''returns title url from result node'''
        return parse_qs(urlparse(node.a['href']).query)['q']

    def parse_link(self, node):
        '''returns parsed link dictionary'''
        return {
            'title': self.parse_title(node),
            'snippet': self.parse_snippet(node),
            'url': self.parse_url(node),
        }

    def get_html(self):
        '''returns prettyfied html from soup'''
        return self.soup.prettify()

    def get_next_page(self):
        '''returns next page url or None'''
        try:
            return self.parse_next_page()
        except IndexError:
            pass

    def get_links(self):
        '''returns parsed link dictionaries'''
        links = []
        for node in self.parse_links():
            links.append(self.parse_link(node))
        return links


class GoogleScraper(object):

    '''follows next page and extracts links'''

    def __init__(self, search, user_agent=None, proxy=None):
        self.url = search.url
        self.start = 1
        self.search = search
        self.user_agent = user_agent

    def sleep(self):
        '''sleeps TIMEOUT_BETWEEN_RETRIES seconds'''
        print(
            'sleeping for {} seconds'.format(settings.TIMEOUT_BETWEEN_RETRIES)
        )
        time.sleep(settings.TIMEOUT_BETWEEN_RETRIES)

    def update_proxy(self):
        '''updates instance proxy'''
        from .models import Proxy
        old_proxy = self.proxy
        self.proxy = Proxy.get_proxy()
        print('switching proxy from {} to {}'.format(old_proxy, self.proxy))
        self.sleep()

    def get_request_params(self):
        '''returns request call parameters to be unpacked.'''
        request_params = {'url': self.url, 'timeout': settings.REQUEST_TIMEOUT}
        if self.user_agent:
            request_params['headers'] = {'User-Agent': self.user_agent.string}
        if self.proxy:
            request_params['proxies'] = {
                'http': 'http://{}:{}'.format(self.proxy.host, self.proxy.port)
            }
        return request_params

    def get_response(self):
        '''gets http response for url or None.'''
        try:
            self.proxy.register()
            response = requests.get(**self.get_request_params())
            self.proxy.unregister()
            print('got response from url {}'.format(self.url))
            self.proxy.set_online()
            return response
        except requests.ConnectionError as e:
            print('connection failed {}'.format(e))
        except requests.Timeout as e:
            print('connection timeout {}'.format(e))
        self.proxy.unset_online()
        self.update_proxy()
        print('failed to get response from url {}'.format(self.url))

    def handle_status_code(self):
        '''
        gets http response or None if response status code not equal to 200
        '''
        if self.response.status_code == 200:
            print('status code 200 for {}'.format(self.url))
            self.proxy.unset_google_ban()
            return self.response
        print(
            'bad status code {} for {}'.format(
                self.response.status_code, self.url
            )
        )
        self.proxy.set_google_ban()
        self.update_proxy()

    def do_request(self):
        '''performs http request and handles exceptions'''
        for i in range(settings.MAX_RETRIES):
            self.response = self.get_response()
            if not self.response:
                print('retrying for {} time'.format(i + 1))
                continue
            self.response = self.handle_status_code()
            if not self.response:
                print('retrying for {} time'.format(i + 1))
                continue
            self.parser = GoogleParser(self.response)
            break

    def get_end(self):
        '''returns end result index'''
        return self.start + settings.RESULTS_PER_PAGE

    def create_page(self):
        '''creates GooglePage entry in database'''
        from .models import GooglePage
        self.page = GooglePage.objects.create(
            search=self.search,
            url=self.url,
            html=self.get_html(),
            start=self.start,
            end=self.get_end(),
            next_page=self.parser.get_next_page()
        )
        print('created google page {}'.format(self.page))

    def create_links(self):
        '''creates GoogleLink entries in database'''
        from .models import GoogleLink
        self.links = []
        for link_params, i in enumerate(self.parser.get_links()):
            link_params.update({'page': self.page, 'rank': self.start + i})
            link = GoogleLink.objects.create(**link_params)
            print('created google link {}'.format(link))
            self.links.append(link)
        print(
            'created {} google links for google page {}'.format(
                len(self.links), self.page
            )
        )

    def scrape(self):
        '''main scrape call'''
        print('scraping for query {}'.format(self.search))
        while True:
            self.do_request()
            if not self.response:
                self.search.unset_success()
                break
            self.create_page()
            self.create_links()
            if not self.page.next_page:
                print('reached last page for query {}'.format(self.search))
                self.search.set_success()
                break
            self.url = self.page.next_page
            self.start += settings.RESULTS_PER_PAGE
