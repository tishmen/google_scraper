import random
import socket
import string
import time

from datetime import date
from urllib.parse import urlencode

import GeoIP

from django.conf import settings
from django.db import models
from django.utils import timezone

from .utils import GoogleScraper
from .choices import *


class UserAgent(models.Model):

    '''database record for user agent'''

    string = models.TextField(unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.string

    @staticmethod
    def get_user_agent_string():
        '''return user agent or None'''
        try:
            return UserAgent.objects.order_by('?').first().string
        except AttributeError:
            print('no user agents in database')


class Proxy(models.Model):

    '''database record for proxy'''

    host = models.GenericIPAddressField(protocol='IPv4')
    port = models.PositiveIntegerField()
    online = models.NullBooleanField()
    google_ban = models.NullBooleanField()
    speed = models.FloatField(null=True, blank=True)
    country = models.TextField(null=True, blank=True)
    scraper_count = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_online = models.DateTimeField(null=True, blank=True)
    date_google_ban = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'proxies'
        unique_together = ['host', 'port']

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)

    def save(self, *args, **kwargs):
        self.country_check()
        super(Proxy, self).save(*args, **kwargs)

    @staticmethod
    def get_proxy():
        '''return working proxy with lowest connection count or None'''
        proxies = Proxy.objects.exclude(online=False, google_ban=True)
        return proxies.order_by('-scraper_count').first()

    def register(self):
        '''increment scraper_count before http request'''
        self.scraper_count += 1
        self.save()
        print(
            'proxy {} is connected to {} scrapers'.format(
                self, self.scraper_count
            )
        )

    def unregister(self):
        '''decrement scraper_count after http request'''
        self.scraper_count -= 1
        self.save()
        print(
            'proxy {} is connected to {} scrapers'.format(
                self, self.scraper_count
            )
        )

    def set_online(self, do_save=True):
        '''set proxy status to online'''
        if not self.online:
            self.online = True
        self.date_online = timezone.now()
        if do_save:
            self.save()
        print('proxy {} is online'.format(self))

    def unset_online(self, do_save=True):
        '''set proxy status to offline'''
        if self.online is not False:
            self.online = False
            if do_save:
                self.save()
        print('proxy {} is not online'.format(self))

    def set_google_ban(self):
        '''set proxy status to banned'''
        if not self.google_ban:
            self.google_ban = True
        self.date_google_ban = timezone.now()
        self.save()
        print('proxy {} is banned by google'.format(self))

    def unset_google_ban(self):
        '''set proxy status to unbanned'''
        if self.google_ban is not False:
            self.google_ban = False
            self.save()
        print('proxy {} is not banned by google'.format(self))

    def set_speed(self, time):
        '''set proxy speed to value'''
        self.speed = time
        self.save()
        print('proxy {} speed is {}'.format(self, self.speed))

    def unset_speed(self):
        '''set proxy speed to None'''
        self.speed = None
        self.save()

    def online_check(self):
        '''create connection to the proxy server and record status'''
        print('starting online check for {}'.format(self))
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(settings.PROXY_TIMEOUT)
        try:
            sock.connect((self.host, self.port))
            self.set_online(do_save=False)
            self.set_speed(time.time() - start)
        except (socket.error, socket.timeout):
            self.unset_online(do_save=False)
            self.unset_speed()

    def google_ban_check(self):
        '''send random query to google and record status'''
        self.online_check()
        if not self.online:
            return
        print('starting google ban check for {}'.format(self))
        q = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
        search = GoogleSearch.objects.create(q=q)
        scraper = GoogleScraper(
            search, UserAgent.get_user_agent_string(), self
        )
        scraper.do_request()
        search.delete()

    def country_check(self):
        '''query geoip database for proxy country'''
        if self.country:
            return
        print('starting geoip check for {}'.format(self))
        geoip = GeoIP.open(
            '/usr/local/share/GeoIP/GeoLiteCity.dat', GeoIP.GEOIP_STANDARD
        )
        record = geoip.record_by_addr(self.host)
        if not record:
            return
        self.country = record['country_name']
        self.save()


class GoogleSearch(models.Model):

    '''database record for google search'''

    q = models.CharField(verbose_name='query', max_length=100)
    cr = models.CharField(
        verbose_name='country', max_length=9, choices=SEARCH_CR,
        default='countryUS'
    )
    cd_min = models.DateField(verbose_name='date start', null=True, blank=True)
    cd_max = models.DateField(verbose_name='date end', null=True, blank=True)
    success = models.NullBooleanField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'google searches'

    def __str__(self):
        return self.q

    def save(self, *args, **kwargs):
        if self.cd_min and not self.cd_max:
            self.cd_max = date.today()
        super(GoogleSearch, self).save(*args, **kwargs)

    def set_success(self):
        '''set google search success to True'''
        self.success = True
        self.save()
        print('google search for query {} succeded')

    def unset_success(self):
        '''set google search success to False'''
        self.success = False
        self.save()
        print('google search for query {} failed')

    def get_query_params(self):
        '''return query params to be added to google search url'''
        params = {'q': self.q, 'cr': self.cr, 'hl': 'en', 'nfpr': '1'}
        if settings.RESULTS_PER_PAGE != 10:
            params['num'] = str(settings.RESULTS_PER_PAGE)
        if self.cd_min and self.cd_max:
            cd_min = self.cd_min.strftime('%m/%d/%Y')
            cd_max = self.cd_max.strftime('%m/%d/%Y')
            params['tbs'] = 'cdr:1,cd_min:{},cd_max:{}'.format(cd_min, cd_max)
        return params

    @property
    def url(self):
        '''google search url for query'''
        base = 'https://www.google.com/search?'
        return base + urlencode(self.get_query_params())

    def search(self):
        '''search call on GoogleScraper object'''
        scraper = GoogleScraper(
            self, UserAgent.get_user_agent_string(), Proxy.get_proxy()
        )
        scraper.scrape()


class GooglePage(models.Model):

    '''database record for google page'''

    search = models.ForeignKey('GoogleSearch')
    url = models.URLField()
    html = models.TextField()
    start = models.PositiveIntegerField(default=0)
    end = models.PositiveIntegerField(default=0)
    next_page = models.URLField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url


class GoogleLink(models.Model):

    '''database record for google link'''

    page = models.ForeignKey('GooglePage')
    url = models.URLField()
    title = models.CharField(max_length=100)
    snippet = models.TextField()
    rank = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
