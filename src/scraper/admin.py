from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages

from .models import UserAgent, Proxy, GoogleSearch, GooglePage, GoogleLink
from .tasks import online_check_task, google_ban_check_task, search_task


class UserAgentResource(resources.ModelResource):

    class Meta:
        model = UserAgent
        exclude = ['date_added']


class ProxyResource(resources.ModelResource):

    class Meta:
        model = Proxy
        exclude = [
            'online', 'google_ban', 'date_online', 'date_google_ban', 'speed',
            'country', 'scraper_count', 'date_added', 'date_updated'
        ]


class GoogleSearchResource(resources.ModelResource):

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
    actions = ['online_check_action', 'google_ban_check_action']

    def add_view(self, request, extra_content=None):
        self.exclude = [
            'online', 'google_ban', 'speed', 'country', 'scraper_count',
            'date_added', 'date_updated', 'date_online', 'date_google_ban'
        ]
        self.readonly_fields = []
        return super(ProxyAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        self.readonly_fields = [
            'host', 'port', 'online', 'google_ban', 'speed', 'country',
            'scraper_count', 'date_added', 'date_updated', 'date_online',
            'date_google_ban'
        ]
        self.exclude = []
        return super(ProxyAdmin, self).change_view(request, object_id)

    def online_check_action(self, request, queryset):
        '''online check admin action'''
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
        '''google ban check admin action'''
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


@admin.register(GoogleSearch)
class GoogleSearchAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = GoogleSearchResource
    search_fields = ['q']
    list_display = ['q', 'cr', 'cd_min', 'cd_max', 'success', 'date_updated']
    list_filter = ['success']
    actions = ['search_action']
    exclude = ['success']

    def add_view(self, request, extra_content=None):
        self.readonly_fields = []
        return super(GoogleSearchAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        obj = GoogleSearch.objects.get(id=object_id)
        if obj.success:
            self.readonly_fields = ['q', 'cr', 'cd_min', 'cd_max', 'success']
            self.exclude = []
        return super(GoogleSearchAdmin, self).change_view(request, object_id)

    def search_action(self, request, queryset):
        '''google search admin action'''
        count = queryset.count()
        search_task.delay(queryset)
        if count == 1:
            part = '1 search'
        else:
            part = '{} searches'.format(count)
        self.message_user(
            request,
            'Successfully launched search_task for ' + part,
            level=messages.SUCCESS
        )

    search_action.short_description = 'Search Google for selected searches'
