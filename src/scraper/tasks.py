from celery import shared_task


@shared_task(bind=True)
def _online_check_task(self, proxy):
    '''call online check on proxy object'''
    proxy.online_check()


@shared_task(bind=True)
def _google_ban_check_task(self, proxy):
    '''call google ban check on proxy object'''
    proxy.google_ban_check()


@shared_task(bind=True)
def _search_task(self, google_search):
    '''call search on google search object'''
    google_search.search()


@shared_task(bind=True)
def online_check_task(self, proxies):
    '''process online check tasks async'''
    print('starting online_check_task for {} proxies'.format(proxies.count()))
    for proxy in proxies:
        _online_check_task.delay(proxy)


@shared_task(bind=True)
def google_ban_check_task(self, proxies):
    '''process google ban check tasks async'''
    print(
        'starting google_ban_check_task for {} proxies'.format(proxies.count())
    )
    for proxy in proxies:
        _google_ban_check_task.delay(proxy)


@shared_task(bind=True)
def search_task(self, google_searches):
    '''process search tasks async'''
    print(
        'starting search_task for {} google searches'.format(
            google_searches.count()
        )
    )
    for google_search in google_searches:
        _search_task.delay(google_search)
