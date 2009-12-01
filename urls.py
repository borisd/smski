from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('myproject',
    (r'^$', 'smski.views.index'),
    (r'^new_user/$', 'smski.views.new_user'),
    (r'^user_list/$', 'smski.views.users'),
    (r'^accounts/login/$',  login,  {"template_name": "login.html"}),
    (r'^accounts/logout/$', logout, {"next_page":"/"}),
    (r'^set_phone/(?P<user_id>\d+)/$', 'smski.views.set_phone'),
    (r'^verify_phone/(?P<user_id>\d+)/$', 'smski.views.verify_phone'),
    (r'^friend_request/(?P<user_id>\d+)/$', 'smski.views.friend_request'),
)

