import inspect
import itertools

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


class ReadOnlyInline(admin.TabularInline):

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class GooglePageInline(ReadOnlyInline):

    model = GooglePage
    exclude = ['html', 'start', 'end', 'next_page']
    readonly_fields = ['url', 'date_added']
    extra = 0
    show_change_link = True


class GoogleLinkInline(ReadOnlyInline):

    model = GoogleLink
    exclude = ['snippet', 'rank']
    readonly_fields = ['url', 'title', 'date_added']
    extra = 0


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
    inlines = [GooglePageInline]

    def add_view(self, request, extra_content=None):
        self.readonly_fields = []
        return super(GoogleSearchAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        obj = GoogleSearch.objects.get(id=object_id)
        if obj.success:
            self.readonly_fields = ['q', 'cr', 'cd_min', 'cd_max', 'success']
            self.exclude = []
        return super(GoogleSearchAdmin, self).change_view(request, object_id)

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
        return super(GoogleSearchAdmin, self).render_change_form(
            request, context, *args, **kwargs
        )

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
class GooglePageAdmin(ReadOnlyAdmin):

    list_display = ['url', 'date_added']
    readonly_fields = ['url', 'start', 'end', 'next_page']
    exclude = ['search', 'html']
    inlines = [GoogleLinkInline]


@admin.register(GoogleLink)
class GoogleLinkAdmin(ReadOnlyAdmin):

    search_fields = ['title']
    list_display = ['url', 'title', 'date_added']
    readonly_fields = ['url', 'title', 'snippet', 'rank']
    exclude = ['page']
