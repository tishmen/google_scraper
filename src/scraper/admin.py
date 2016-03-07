import inspect
import itertools

from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages
from django.core.urlresolvers import reverse

from .models import UserAgent, Proxy, GoogleSearch, GooglePage, GoogleLink
from .tasks import online_check_task, google_ban_check_task, search_task


class UserAgentResource(resources.ModelResource):

    'django import export resource class for UserAgent'

    class Meta:
        model = UserAgent
        exclude = ['date_added']


class ProxyResource(resources.ModelResource):

    'django import export resource class for Proxy'

    class Meta:
        model = Proxy
        exclude = [
            'online', 'google_ban', 'date_online', 'date_google_ban', 'speed',
            'country', 'scraper_count', 'date_added', 'date_updated'
        ]


class GoogleSearchResource(resources.ModelResource):

    'django import export resource class for GoogleSearch'

    class Meta:
        model = GoogleSearch
        exclude = ['success', 'date_updated', 'date_added']


class ReadOnlyInline(admin.TabularInline):

    '''inline with add and delete permissions disabled'''

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class GooglePageInline(ReadOnlyInline):

    '''Google page inlined to Google search'''

    model = GooglePage
    exclude = [
        'url', 'html', 'total_result_count', 'result_count', 'start', 'end',
        'next_page'
    ]
    readonly_fields = ['_url', 'date_added']
    extra = 0
    show_change_link = True

    def _url(self, obj):
        '''google page admin change list url'''
        url = reverse(
            'admin:{}_{}_change'.format(
                obj._meta.app_label, obj._meta.model_name
            ),
            args=[obj.id]
        )
        return '<a href="{}">{}</a>'.format(url, obj.url)

    _url.allow_tags = True


class GoogleLinkInline(ReadOnlyInline):

    '''Google link inlined to Google page'''

    model = GoogleLink
    exclude = ['title', 'url', 'snippet']
    readonly_fields = ['_title', '_url', 'rank', 'date_added']
    extra = 0

    def _title(self, obj):
        '''google link admin change list url'''
        url = reverse(
            'admin:{}_{}_change'.format(
                obj._meta.app_label, obj._meta.model_name
            ),
            args=[obj.id]
        )
        return '<a href="{}">{}</a>'.format(url, obj.title)

    _title.allow_tags = True

    def _url(self, obj):
        '''search result url'''
        return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)

    _url.allow_tags = True


class NoInlineTitleAdmin(admin.ModelAdmin):

    '''title removed from tabular inline entry'''

    # http://stackoverflow.com/questions/5086537/how-to-omit-object-name-from-djangos-tabularinline-admin-view
    def render_change_form(self, request, context, *args, **kwargs):
        def get_queryset(original_func):
            def wrapped_func():
                if inspect.stack()[1][3] == '__iter__':
                    return itertools.repeat(None)
                return original_func()
            return wrapped_func
        for formset in context['inline_admin_formsets']:
            formset.formset.get_queryset = get_queryset(
                formset.formset.get_queryset
            )
        return super().render_change_form(
            request, context, *args, **kwargs
        )


class ReadOnlyAdmin(admin.ModelAdmin):

    '''model admin with add and delete permissions disabled'''

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserAgent)
class UserAgentAdmin(ImportMixin, admin.ModelAdmin):

    '''model admin for user agent'''

    resource_class = UserAgentResource
    search_fields = ['string']
    list_display = ['string', 'date_added']


@admin.register(Proxy)
class ProxyAdmin(ImportMixin, admin.ModelAdmin):

    '''model admin for proxy'''

    resource_class = ProxyResource
    search_fields = ['__str__']
    list_display = [
        '__str__', 'scraper_count', 'online', 'google_ban', 'speed', 'country',
        'date_updated'
    ]
    list_filter = ['online', 'google_ban']
    actions = ['online_check_action', 'google_ban_check_action']

    def add_view(self, request, extra_content=None):
        self.fieldsets = [[None, {'fields': ['host', 'port']}]]
        self.readonly_fields = []
        return super().add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        self.fieldsets = [
            [None, {'fields': ['host', 'port', 'scraper_count']}],
            [
                'Status', {
                    'classes': ['collapse'],
                    'fields': [
                        'online', 'google_ban', 'speed', 'date_online',
                        'date_google_ban'
                    ]
                }
            ],
            ['Location', {'classes': ['collapse'], 'fields': ['country']}]
        ]
        self.readonly_fields = [
            'host', 'port', 'scraper_count', 'online', 'google_ban', 'speed',
            'date_online', 'date_google_ban', 'country'
        ]
        return super().change_view(request, object_id)

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
class GoogleSearchAdmin(ImportMixin, NoInlineTitleAdmin):

    '''model admin for google search'''

    resource_class = GoogleSearchResource
    search_fields = ['q']
    list_display = ['q', '_results', 'result_count', 'success', 'date_updated']
    list_filter = ['success']
    actions = ['search_action']

    def add_view(self, request, extra_content=None):
        self.fieldsets = [
            [None, {'fields': ['q']}],
            [
                'Options', {
                    'classes': ['collapse'],
                    'fields': ['cr', 'cd_min', 'cd_max']
                }
            ]
        ]
        self.readonly_fields = []
        self.inlines = []
        return super().add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        self.fieldsets = [
            [None, {'fields': ['q']}],
            [
                'Options', {
                    'classes': ['collapse'],
                    'fields': ['cr', 'cd_min', 'cd_max']
                }
            ]
        ]
        self.readonly_fields = []
        self.inlines = []
        obj = GoogleSearch.objects.get(id=object_id)
        if obj.result_count:
            self.fieldsets = [
                [None, {'fields': ['q']}],
                [
                    'Options', {
                        'classes': ['collapse'],
                        'fields': ['cr', 'cd_min', 'cd_max']
                    }
                ],
                [
                    'Results', {
                        'classes': ['collapse'],
                        'fields': ['success', 'result_count']
                    }
                ]
            ]
            self.readonly_fields = [
                'q', 'cr', 'cd_min', 'cd_max', 'success', 'result_count'
            ]
            self.inlines = [GooglePageInline]
        return super().change_view(request, object_id)

    def search_action(self, request, queryset):
        '''google search admin action'''
        queryset = queryset.exclude(success=True)
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

    def _results(self, obj):
        '''google link admin change list url filtered by search id'''
        url = reverse('admin:scraper_googlelink_changelist') + \
            '?page__search__id__exact={}'.format(obj.id)
        return '<a href="{0}">View all</a>'.format(url)

    _results.short_description = 'results'
    _results.allow_tags = True


@admin.register(GooglePage)
class GooglePageAdmin(NoInlineTitleAdmin, ReadOnlyAdmin):

    '''model admin for google page'''

    list_display = ['url', 'result_count', 'date_added']
    fieldsets = [
        [
            None,
            {'fields': ['_url', '_html', 'total_result_count', 'result_count']}
        ]
    ]
    readonly_fields = ['_url', '_html', 'total_result_count', 'result_count']
    inlines = [GoogleLinkInline]

    def _url(self, obj):
        '''search result page url'''
        return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)

    _url.short_description = 'url'
    _url.allow_tags = True

    def _html(self, obj):
        '''stored html url'''
        return '<a href="{}" target="_blank">View</a>'.format(
            reverse('html', args=[obj.pk])
        )

    _html.short_description = 'html'
    _html.allow_tags = True


@admin.register(GoogleLink)
class GoogleLinkAdmin(ReadOnlyAdmin):

    '''model admin for google link'''

    search_fields = ['title']
    list_display = ['url', 'title', 'date_added']
    fieldsets = [[None, {'fields': ['_url', 'title', 'snippet', 'rank']}]]
    readonly_fields = ['_url', 'title', 'snippet', 'rank']

    def lookup_allowed(self, key, value):
        if key in ['page__search__id__exact']:
            return True
        return super().lookup_allowed(key, value)

    def _url(self, obj):
        '''search result url'''
        return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)

    _url.short_description = 'url'
    _url.allow_tags = True
