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
            'online', 'google_ban', 'date_online', 'date_google_ban', 'speed',
            'region', 'country', 'latitude', 'longitude', 'scraper_count',
            'date_added', 'date_modified'
        ]


class SearchResource(resources.ModelResource):

    class Meta:
        model = GoogleSearch
        exclude = ['success', 'date_updated', 'date_added']


@admin.register(UserAgent)
class UserAgentAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = UserAgentResource
    search_fields = ['string']
    list_display = ['string', 'date_added']


@admin.register(Proxy)
class ProxyAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = ProxyResource
    search_fields = ['__str__']
    list_display = ['__str__']
