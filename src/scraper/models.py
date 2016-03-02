import random
import socket
import string
import time

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

    class Meta:
        ordering = ['-date_added']

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

    city = models.TextField(null=True, blank=True)
    country = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    scraper_count = models.PositiveIntegerField(default=0)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_online = models.DateTimeField(null=True, blank=True)
    date_google_ban = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'proxies'
        unique_together = ['host', 'port']
        ordering = ['-date_updated']

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)

    def save(self, *args, **kwargs):
        self.geoip_check()
        super(Proxy, self).save(*args, **kwargs)

    @staticmethod
    def get_proxy():
        '''return working proxy with lowest connection count or None'''
        proxies = Proxy.objects.exclude(online=False, google_ban=True)
        return proxies.order_by('-connection_count').first()

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

    def set_online(self):
        '''set proxy status to online'''
        if not self.online:
            self.online = True
        self.date_online = timezone.now()
        self.save()
        print('proxy {} is online'.format(self))

    def unset_online(self):
        '''set proxy status to offline'''
        if self.online:
            self.online = False
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
        if self.google_ban:
            self.google_ban = False
            self.save()
        print('proxy {} is not banned by google'.format(self))

    def online_check(self):
        '''create connection to the proxy server and record status'''
        print('starting online check for {}'.format(self))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
            self.set_online()
        except socket.error:
            self.unset_online()

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

    def speed_check(self):
        '''create connection to the proxy server and record speed'''
        print('starting speed check for {}'.format(self))
        start = time.time()
        self.online_check()
        self.speed = time.time() - start
        self.save()

    def geoip_check(self):
        '''query geoip database if no previous record exists'''
        if self.region or self.country or self.latitude or self.longitude:
            return
        print('starting geoip check for {}'.format(self))
        geoip = GeoIP.open(
            '/usr/local/share/GeoIP/GeoLiteCity.dat', GeoIP.GEOIP_STANDARD
        )
        record = geoip.record_by_addr(self.host)
        if not record:
            return
        self.city = record['city']
        self.country = record['country_name']
        self.latitude = record['latitude']
        self.longitude = record['longitude']
        self.save()


class GoogleSearch(models.Model):

    '''database record for google search'''

    q = models.CharField(verbose_name='query', max_length=100)
    cr = models.CharField(
        verbose_name='country', max_length=9, choices=SEARCH_CR,
        default='countryUS'
    )
    qdr = models.CharField(
        verbose_name='time period', max_length=3, null=True, blank=True
    )

    success = models.NullBooleanField()

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'google searches'
        ordering = ['-date_updated']

    def __str__(self):
        return self.q

    def get_GET_params(self):
        '''return GET params to be added to google search url'''
        params = {'hl': 'en', 'nfpr': '1'}
        if settings.RESULTS_PER_PAGE != 10:
            params['num'] = str(settings.RESULTS_PER_PAGE)
        if self.qdr:
            params['tbs'] = 'qdr:{}'.format(self.qdr)
        for field in self._meta.get_fields():
            name = field.name
            if name in ['id', 'date_added']:
                continue
            value = getattr(self, name)
            if not value:
                continue
            params[name] = value
        return params

    @property
    def url(self):
        '''google search url for query'''
        base = 'https://www.google.com/search?'
        return base + urlencode(self.get_GET_params())

    def search(self):
        '''search call on GoogleScraper object'''
        scraper = GoogleScraper(
            self, UserAgent.get_random_user_agent(), Proxy.get_proxy()
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

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return self.url


class GoogleLink(models.Model):

    '''database record for google link'''

    page = models.ForeignKey('GooglePage')
    title = models.CharField(max_length=100)
    snippet = models.TextField()
    url = models.URLField()
    rank = models.IntegerField()

    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return self.title
