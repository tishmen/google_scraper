import inspect
import itertools

from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages
from django.core.urlresolvers import reverse

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


class ReadOnlyInline(admin.TabularInline):

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class GooglePageInline(ReadOnlyInline):

    model = GooglePage
    exclude = ['url', 'html', 'start', 'end', 'next_page']
    readonly_fields = ['_url', 'date_added']
    extra = 0
    show_change_link = True

    def _url(self, obj):
        url = reverse(
            'admin:{}_{}_change'.format(
                obj._meta.app_label, obj._meta.model_name
            ),
            args=[obj.id]
        )
        return '<a href="{}">{}</a>'.format(url, obj.url)

    _url.allow_tags = True


class GoogleLinkInline(ReadOnlyInline):

    model = GoogleLink
    exclude = ['title', 'url', 'snippet']
    readonly_fields = ['_title', '_url', 'rank', 'date_added']
    extra = 0

    def _title(self, obj):
        url = reverse(
            'admin:{}_{}_change'.format(
                obj._meta.app_label, obj._meta.model_name
            ),
            args=[obj.id]
        )
        return '<a href="{}">{}</a>'.format(url, obj.title)

    _title.allow_tags = True

    def _url(self, obj):
        return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)

    _url.allow_tags = True


class NoInlineTitleAdmin(admin.ModelAdmin):

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

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
        return super().add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        self.readonly_fields = [
            'host', 'port', 'online', 'google_ban', 'speed', 'country',
            'scraper_count', 'date_added', 'date_updated', 'date_online',
            'date_google_ban'
        ]
        self.exclude = []
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

    resource_class = GoogleSearchResource
    search_fields = ['q']
    list_display = ['q', 'cr', 'cd_min', 'cd_max', 'success', 'date_updated']
    list_filter = ['success']
    actions = ['search_action']

    def add_view(self, request, extra_content=None):
        self.readonly_fields = []
        self.exclude = ['success']
        self.inlines = []
        return super().add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        self.readonly_fields = []
        self.exclude = ['success']
        self.inlines = []
        obj = GoogleSearch.objects.get(id=object_id)
        if obj.googlepage_set.count():
            self.exclude = []
            self.readonly_fields = ['q', 'cr', 'cd_min', 'cd_max', 'success']
            self.inlines = [GooglePageInline]
        return super().change_view(request, object_id)

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


@admin.register(GooglePage)
class GooglePageAdmin(NoInlineTitleAdmin, ReadOnlyAdmin):

    list_display = ['url', 'date_added']
    readonly_fields = ['_url', '_html']
    exclude = ['search', 'url', 'html', 'start', 'end', 'next_page']
    inlines = [GoogleLinkInline]

    def _url(self, obj):
        return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)

    _url.short_description = 'url'
    _url.allow_tags = True

    def _html(self, obj):
        return '<a href="{}" target="_blank">View</a>'.format(
            reverse('html', args=[obj.pk])
        )

    _html.short_description = 'html'
    _html.allow_tags = True


@admin.register(GoogleLink)
class GoogleLinkAdmin(ReadOnlyAdmin):

    search_fields = ['title']
    list_display = ['url', 'title', 'date_added']
    readonly_fields = ['_url', 'title', 'snippet', 'rank']
    exclude = ['page', 'url']

    def _url(self, obj):
        return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)

    _url.short_description = 'url'
    _url.allow_tags = True
