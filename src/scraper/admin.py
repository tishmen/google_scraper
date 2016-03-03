from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages

from .models import UserAgent, Proxy, GoogleSearch, GooglePage, GoogleLink
from .tasks import online_check_task, google_ban_check_task, speed_check_task


class UserAgentResource(resources.ModelResource):

    class Meta:
        model = UserAgent
        exclude = ['date_added']


class ProxyResource(resources.ModelResource):

    class Meta:
        model = Proxy
        exclude = [
            'online', 'google_ban', 'date_online', 'date_google_ban', 'speed',
            'city', 'country', 'latitude', 'longitude', 'scraper_count',
            'date_added', 'date_updated'
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
    list_display = [
        '__str__', 'online', 'google_ban', 'speed', 'country', 'scraper_count',
        'date_updated'
    ]
    list_filter = ['online', 'google_ban']
    readonly_fields = [
        'host', 'port', 'online', 'google_ban', 'speed', 'city', 'country',
        'latitude', 'longitude', 'scraper_count', 'date_added', 'date_updated',
        'date_online', 'date_google_ban'
    ]
    actions = ['online_check_action', 'google_ban_check_action']

    # raise an issue on github. ImportMixin does not show import button if user
    # has no add permission
    # def has_add_permission(self, request):
    #     return False

    def online_check_action(self, request, queryset):
        count = queryset.count()
        online_check_task.delay(queryset)
        if count == 1:
            part = '1 proxy'
        else:
            part = '{} proxies'.format(count)
        self.message_user(
            request,
            'Successfully launched online_check_task for ' + part,
            level=messages.SUCCESS
        )

    online_check_action.short_description = 'Check if selected proxies are on'\
        'line'

    def google_ban_check_action(self, request, queryset):
        count = queryset.count()
        google_ban_check_task.delay(queryset)
        if count == 1:
            part = '1 proxy'
        else:
            part = '{} proxies'.format(count)
        self.message_user(
            request,
            'Successfully launched google_ban_check_task for ' + part,
            level=messages.SUCCESS
        )

    google_ban_check_action.short_description = 'Check if selected proxies ar'\
        'e banned by Google'
