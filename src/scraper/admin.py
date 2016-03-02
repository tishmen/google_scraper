from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin

from .models import UserAgent, Proxy, GoogleSearch, GooglePage, GoogleLink


class UserAgentResource(resources.ModelResource):

    class Meta:
        model = UserAgent
        exclude = ['date_added']


class ProxyResource(resources.ModelResource):

    class Meta:
        model = Proxy
        exclude = [
            'online', 'google_ban', 'last_date_online', 'last_date_google_ban',
            'region', 'country', 'latitude', 'longitude', 'scraper_count',
            'date_added', 'date_modified'
        ]


class SearchResource(resources.ModelResource):

    class Meta:
        model = GoogleSearch
        exclude = ['date_added']
