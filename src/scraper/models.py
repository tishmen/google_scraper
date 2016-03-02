from django.db import models

from .choices import *


class UserAgent(models.Model):

    '''database record for user agent'''

    string = models.TextField(unique=True)

    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.string


class Proxy(models.Model):

    '''database record for proxy'''

    host = models.GenericIPAddressField(protocol='IPv4')
    port = models.PositiveIntegerField()

    online = models.NullBooleanField()
    google_ban = models.NullBooleanField()
    last_date_online = models.DateTimeField(null=True, blank=True)
    last_date_google_ban = models.DateTimeField(null=True, blank=True)

    region = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    scraper_count = models.PositiveIntegerField(default=0)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'proxies'
        unique_together = ['host', 'port']

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)


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

    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'google searches'

    def __str__(self):
        return self.q


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
    title = models.CharField(max_length=100)
    snippet = models.TextField()
    url = models.URLField()
    rank = models.IntegerField()

    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
