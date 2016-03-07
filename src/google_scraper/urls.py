from django.conf.urls import url
from django.contrib import admin

from scraper import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^html/(?P<pk>\d+)$', views.html_view, name='html'),
]
