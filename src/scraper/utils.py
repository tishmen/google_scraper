import random
import time

import htmlmin
import requests

from bs4 import BeautifulSoup

from django.conf import settings


class GoogleParser(object):

    '''parses the response from google'''

    def __init__(self, response):
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def parse_links(self):
        '''returns result nodes that contain snippet node'''
        return [node.parent for node in self.soup.select('.srg .rc')]

    def parse_url(self, node):
        '''returns title url from result node'''
        return node.a['href']

    def parse_title(self, node):
        '''returns title text from result node'''
        return node.a.get_text()

    def parse_snippet(self, node):
        '''returns snippet text from result node'''
        return node.select_one('.st').get_text()

    def parse_link(self, node):
        '''returns parsed link dictionary'''
        return {
            'url': self.parse_url(node),
            'title': self.parse_title(node),
            'snippet': self.parse_snippet(node),
        }

    def parse_total_result_count(self):
        '''returns total result count'''
        count = self.soup.select_one('#resultStats').get_text().split(' ')[-4]
        return int(count.replace(',', ''))

    def parse_next_page(self):
        '''returns next page url or None'''
        next_page = self.soup.select('.pn')[-1]
        if next_page.get_text() == 'Next':
            return 'https://www.google.com' + next_page['href']

    def get_html(self):
        '''returns minifyfied html from soup'''
        return htmlmin.minify(str(self.soup))

    def get_links(self):
        '''returns parsed link dictionaries'''
        links = []
        for node in self.parse_links():
            links.append(self.parse_link(node))
        return links

    def get_total_result_count(self):
        '''returns total result count or None'''
        try:
            return self.parse_total_result_count()
        except:
            pass

    def get_next_page(self):
        '''returns next page url or None'''
        try:
            return self.parse_next_page()
        except IndexError:
            pass


class GoogleScraper(object):

    '''follows next page and extracts links'''

    def __init__(self, search, user_agent=None, proxy=None):
        self.success = False
        self.url = search.url
        self.search_result_count = 0
        self.page_result_count = 0
        self.start = 1
        self.search = search
        self.user_agent = user_agent
        self.proxy = proxy

    def sleep(self, seconds):
        '''sleeps n seconds'''
        print('sleeping for {} seconds'.format(seconds))
        time.sleep(seconds)

    def update_proxy(self):
        '''updates instance proxy'''
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
        '''returns request call parameters to be unpacked.'''
        request_params = {'url': self.url, 'timeout': settings.REQUEST_TIMEOUT}
        if self.user_agent:
            request_params['headers'] = {'User-Agent': self.user_agent}
        if self.proxy:
            request_params['proxies'] = {
                'http': 'http://{}:{}'.format(self.proxy.host, self.proxy.port)
            }
        return request_params

    def _get_response(self):
        '''gets http response for url'''
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

    def get_response(self):
        '''gets http response for url or None.'''
        try:
            return self._get_response()
        except requests.ConnectionError as e:
            print('connection failed {}'.format(e))
        except requests.Timeout as e:
            print('connection timeout {}'.format(e))
        if self.proxy:
            self.proxy.unset_online()
            self.update_proxy()
        print('failed to get response from url {}'.format(self.url))

    def handle_status_code(self):
        '''
        gets http response or None if response status code not equal to 200
        '''
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
        '''performs http request and handles exceptions'''
        for i in range(settings.MAX_RETRY):
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

    def get_links(self):
        '''gets link array from parser and adjusts result count'''
        self.links = self.parser.get_links()
        self.page_result_count = len(self.links)

    def get_end(self):
        '''returns end result index'''
        return self.start + self.page_result_count

    def create_page(self):
        '''creates GooglePage entry in database'''
        from .models import GooglePage
        self.page = GooglePage.objects.create(
            search=self.search,
            url=self.url,
            html=self.parser.get_html(),
            total_result_count=self.parser.get_total_result_count(),
            result_count=self.page_result_count,
            start=self.start,
            end=self.get_end(),
            next_page=self.parser.get_next_page()
        )
        print('created google page {}'.format(self.page))

    def create_links(self):
        '''creates GoogleLink entries in database'''
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
        '''checks for valid response'''
        if self.response:
            return False
        self.success = False
        return True

    def is_last_page(self):
        '''checks whether we are on the last page of search results'''
        if self.page.next_page:
            return
        print('reached last page for query {}'.format(self.search))
        self.success = True
        return True

    def update_loop(self):
        '''updates main scrape loop'''
        self.url = self.page.next_page
        self.search_result_count += self.page_result_count
        self.start = self.get_end()
        self.success = True

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
            self.sleep(
                random.uniform(
                    settings.MIN_RETRY_SLEEP, settings.MAX_RETRY_SLEEP
                )
            )
        self.search.set_result_count(self.search_result_count)
        self.search.set_success(self.success)
