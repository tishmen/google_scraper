from celery import shared_task
from celery.utils.log import get_task_logger

from .models import Proxy

logger = get_task_logger(__name__)


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
def online_check_task(self, proxies=None):
    '''process online check tasks async'''
    if not proxies:
        proxies = Proxy.objects.all()
    logger.info(
        'starting online_check_task for {} proxies'.format(proxies.count())
    )
    for proxy in proxies:
        _online_check_task.delay(proxy)


@shared_task(bind=True)
def google_ban_check_task(self, proxies=None):
    '''process google ban check tasks async'''
    if not proxies:
        proxies = Proxy.objects.all()
    logger.info(
        'starting google_ban_check_task for {} proxies'.format(proxies.count())
    )
    for proxy in proxies:
        _google_ban_check_task.delay(proxy)


@shared_task(bind=True)
def search_task(self, searches):
    '''process search tasks async'''
    logger.info(
        'starting search_task for {} google searches'.format(searches.count())
    )
    for search in searches:
        _search_task.delay(search)
